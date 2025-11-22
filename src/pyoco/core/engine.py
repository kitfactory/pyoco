import time
from typing import Dict, Any, List, Set
from .models import Flow, Task
from .context import Context
from ..trace.backend import TraceBackend
from ..trace.console import ConsoleTraceBackend

class Engine:
    """
    The core execution engine for Pyoco flows.
    
    Responsible for:
    - Resolving task dependencies
    - Managing parallel execution (using ThreadPoolExecutor)
    - Handling input injection and artifact storage
    - Delegating logging to the TraceBackend
    
    Intentionally keeps scheduling logic simple (no distributed queue, no external DB).
    """
    def __init__(self, trace_backend: TraceBackend = None):
        self.trace = trace_backend or ConsoleTraceBackend()

    def run(self, flow: Flow, params: Dict[str, Any] = None) -> Context:
        ctx = Context(params=params or {})
        self.trace.on_flow_start(flow.name)
        
        executed: Set[Task] = set()
        running: Set[Any] = set() # Set of Futures
        
        import concurrent.futures
        
        # Use ThreadPoolExecutor for parallel execution
        # Max workers could be configurable, default to something reasonable
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_task = {}
            task_deadlines: Dict[Task, float] = {}
            
            failed: Set[Task] = set()

            while len(executed) + len(failed) < len(flow.tasks):
                # Identify runnable tasks
                runnable = []
                for task in flow.tasks:
                    if task in executed or task in failed or task in [future_to_task[f] for f in running]:
                        continue
                    
                    # Check dependencies
                    deps_met = True
                    
                    if task.trigger_policy == "ANY":
                        # OR-join: Run if ANY dependency is executed (and successful)
                        # But what if all failed? Then we can't run.
                        # If at least one succeeded, we run.
                        # If none succeeded yet, we wait.
                        # If all failed, we fail (or skip).
                        
                        any_success = False
                        all_failed = True
                        
                        if not task.dependencies:
                            # No deps = ready
                            any_success = True
                            all_failed = False
                        else:
                            for dep in task.dependencies:
                                if dep in executed:
                                    any_success = True
                                    all_failed = False
                                    break # Found one success
                                if dep not in failed:
                                    all_failed = False # At least one is still running/pending
                        
                        if any_success:
                            deps_met = True
                        elif all_failed:
                            # All deps failed, so we fail/skip
                            failed.add(task)
                            deps_met = False
                            # Continue to next task loop to avoid adding to runnable
                            continue 
                        else:
                            # Still waiting
                            deps_met = False

                    else:
                        # ALL (AND-join) - Default
                        for dep in task.dependencies:
                            if dep in failed:
                                # Dependency failed
                                if task.fail_policy == "isolate" or dep.fail_policy == "isolate": 
                                    failed.add(task)
                                    deps_met = False
                                    break
                                else:
                                    pass # fail=stop handled elsewhere
                            
                            if dep not in executed:
                                deps_met = False
                                break
                    
                    if deps_met and task not in failed:
                        runnable.append(task)
                
                # If no runnable tasks and no running tasks, we are stuck
                # But if we have failed tasks, maybe that's why?
                if not runnable and not running:
                    if len(executed) + len(failed) == len(flow.tasks):
                        # All done (some failed)
                        break
                    raise RuntimeError("Deadlock or cycle detected in workflow")
                
                # Submit runnable tasks
                for task in runnable:
                    future = executor.submit(self._execute_task, task, ctx)
                    running.add(future)
                    future_to_task[future] = task
                    # Record start time for timeout tracking
                    # We need to track start times or deadlines.
                    # Let's store deadline in a separate dict or attach to task?
                    # Task is immutable-ish (dataclass).
                    # Let's use a dict.
                    if task.timeout_sec:
                         task_deadlines[task] = time.time() + task.timeout_sec

                # Calculate wait timeout
                wait_timeout = None
                if task_deadlines:
                    now = time.time()
                    min_deadline = min(task_deadlines.values())
                    wait_timeout = max(0, min_deadline - now)
                
                # Wait for at least one task to complete or timeout
                if running:
                    done, _ = concurrent.futures.wait(
                        running, 
                        timeout=wait_timeout,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    
                    # Check for timeouts first
                    now = time.time()
                    timed_out_tasks = []
                    for task, deadline in list(task_deadlines.items()):
                        if now >= deadline:
                            # Task timed out
                            # Find the future for this task
                            # This is inefficient, but running set is small
                            found_future = None
                            for f, t in future_to_task.items():
                                if t == task and f in running:
                                    found_future = f
                                    break
                            
                            if found_future:
                                timed_out_tasks.append(found_future)
                                # Remove from tracking
                                running.remove(found_future)
                                del task_deadlines[task]
                                
                                # Handle failure
                                if task.fail_policy == "isolate":
                                    failed.add(task)
                                    self.trace.on_node_error(task.name, TimeoutError(f"Task exceeded timeout of {task.timeout_sec}s"))
                                else:
                                    raise TimeoutError(f"Task '{task.name}' exceeded timeout of {task.timeout_sec}s")

                    for future in done:
                        if future in running: # Might have been removed by timeout check above (unlikely if wait returned due to completion, but possible race)
                            running.remove(future)
                            task = future_to_task[future]
                            if task in task_deadlines:
                                del task_deadlines[task]
                                
                            try:
                                future.result() # Re-raise exception if any
                                executed.add(task)
                            except Exception as e:
                                if task.fail_policy == "isolate":
                                    failed.add(task)
                                    self.trace.on_node_error(task.name, e) # Log it
                                else:
                                    # fail=stop (default)
                                    raise e

        self.trace.on_flow_end(flow.name)
        return ctx

    def _execute_task(self, task: Task, ctx: Context):
        self.trace.on_node_start(task.name)
        start_time = time.time()
        # Retry loop
        retries_left = task.retries
        while True:
            try:
                # Resolve inputs from task configuration
                kwargs = {}
                for key, value in task.inputs.items():
                    kwargs[key] = ctx.resolve(value)
                
                # Inspect function signature to inject 'ctx' if needed
                import inspect
                sig = inspect.signature(task.func)
                
                # Inject 'ctx' if requested
                if 'ctx' in sig.parameters:
                    kwargs['ctx'] = ctx
                
                # Auto-wiring (legacy/convenience)
                for param_name in sig.parameters:
                    if param_name in kwargs:
                        continue
                    if param_name == 'ctx': 
                        continue 
                    
                    if param_name in ctx.params:
                        kwargs[param_name] = ctx.params[param_name]
                    elif param_name in ctx.results:
                        kwargs[param_name] = ctx.results[param_name]
                
                result = task.func(**kwargs)
                ctx.set_result(task.name, result)
                
                # Handle outputs saving
                for target_path in task.outputs:
                    parts = target_path.split(".")
                    root_name = parts[0]
                    root_obj = None
                    if root_name == "scratch":
                        root_obj = ctx.scratch
                    elif root_name == "results":
                        root_obj = ctx.results
                    elif root_name == "params":
                        root_obj = ctx.params
                    
                    if root_obj is not None:
                        current = root_obj
                        for i, part in enumerate(parts[1:-1]):
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                            if not isinstance(current, dict):
                                    break
                        else:
                            current[parts[-1]] = result

                duration = (time.time() - start_time) * 1000
                self.trace.on_node_end(task.name, duration)
                return # Success
                
            except Exception as e:
                if retries_left > 0:
                    retries_left -= 1
                    # Log retry?
                    # self.trace.on_node_retry(task.name, e, retries_left) # If method exists
                    # For now just continue
                    time.sleep(0.1) # Small backoff?
                    continue
                else:
                    self.trace.on_node_error(task.name, e)
                    raise e
