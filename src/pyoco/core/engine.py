import time
import io
import sys
import traceback
from typing import Dict, Any, List, Set, Optional
import contextlib
from .models import Flow, Task, RunContext, TaskState, RunStatus
from .context import Context, LoopFrame
from .exceptions import UntilMaxIterationsExceeded
from ..trace.backend import TraceBackend
from ..trace.console import ConsoleTraceBackend
from ..dsl.nodes import TaskNode, RepeatNode, ForEachNode, UntilNode, SwitchNode, DEFAULT_CASE_VALUE
from ..dsl.expressions import Expression

class TeeStream:
    def __init__(self, original):
        self.original = original
        self.buffer = io.StringIO()

    def write(self, data):
        self.original.write(data)
        self.buffer.write(data)
        return len(data)

    def flush(self):
        self.original.flush()

    def getvalue(self):
        return self.buffer.getvalue()

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
        # Track active runs: run_id -> RunContext
        from .models import RunContext
        self.active_runs: Dict[str, RunContext] = {}

    def get_run(self, run_id: str) -> Any:
        # Return RunContext if active, else None (for now)
        return self.active_runs.get(run_id)

    def cancel(self, run_id: str):
        """
        Cancel an active run.
        """
        from .models import RunStatus
        run_ctx = self.active_runs.get(run_id)
        if run_ctx:
            if run_ctx.status == RunStatus.RUNNING:
                run_ctx.status = RunStatus.CANCELLING
                # We don't force kill threads here, the loop will handle it.

    def run(self, flow: Flow, params: Dict[str, Any] = None, run_context: Optional[RunContext] = None) -> Context:
        # Initialize RunContext (v0.2.0)
        if run_context is None:
            run_context = RunContext()
        
        run_ctx = run_context
        run_ctx.flow_name = flow.name
        run_ctx.params = params or {}
        
        # Initialize all tasks as PENDING
        for task in flow.tasks:
            run_ctx.tasks[task.name] = TaskState.PENDING
            run_ctx.ensure_task_record(task.name)
            
        ctx = Context(params=params or {}, run_context=run_ctx)
        self.trace.on_flow_start(flow.name, run_id=run_ctx.run_id)
        
        # Register active run
        self.active_runs[run_ctx.run_id] = run_ctx

        if flow.has_control_flow():
            try:
                program = flow.build_program()
                self._execute_subflow(program, ctx)
                run_ctx.status = RunStatus.COMPLETED
            except Exception:
                run_ctx.status = RunStatus.FAILED
                run_ctx.end_time = time.time()
                raise
            run_ctx.end_time = time.time()
            return ctx
        
        try:
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
                    # Check for cancellation
                    if run_ctx.status in [RunStatus.CANCELLING, RunStatus.CANCELLED]:
                        # Stop submitting new tasks
                        # Mark all PENDING tasks as CANCELLED
                        for t_name, t_state in run_ctx.tasks.items():
                            if t_state == TaskState.PENDING:
                                run_ctx.tasks[t_name] = TaskState.CANCELLED
                        
                        # If no running tasks, we are done
                        if not running:
                            run_ctx.status = RunStatus.CANCELLED
                            break
                        # Else continue loop to wait for running tasks (graceful shutdown)
                        # We still need to wait, so we fall through to the wait logic,
                        # but 'runnable' will be empty because we won't add anything.
                    
                    # Identify runnable tasks
                    runnable = []
                    if run_ctx.status == RunStatus.RUNNING:
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
                                    run_ctx.tasks[task.name] = TaskState.FAILED
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
                                            run_ctx.tasks[task.name] = TaskState.FAILED # Mark as FAILED (or SKIPPED if we had it)
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
                        
                        run_ctx.status = RunStatus.FAILED
                        run_ctx.end_time = time.time()
                        raise RuntimeError("Deadlock or cycle detected in workflow")
                    
                    # Submit runnable tasks
                    for task in runnable:
                        future = executor.submit(self._execute_task, task, ctx)
                        running.add(future)
                        future_to_task[future] = task
                        # Record start time for timeout tracking
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
                                        run_ctx.tasks[task.name] = TaskState.FAILED
                                        self.trace.on_node_error(task.name, TimeoutError(f"Task exceeded timeout of {task.timeout_sec}s"))
                                    else:
                                        run_ctx.status = RunStatus.FAILED
                                        run_ctx.end_time = time.time()
                                        raise TimeoutError(f"Task '{task.name}' exceeded timeout of {task.timeout_sec}s")

                        for future in done:
                            if future in running: # Might have been removed by timeout check above
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
                                        # TaskState update is handled in _execute_task on exception? 
                                        # No, _execute_task raises. So we need to update here if it failed.
                                        # Actually _execute_task updates to FAILED before raising?
                                        # Let's check _execute_task implementation below.
                                        # If _execute_task raises, we catch it here.
                                        # We should ensure FAILED state.
                                        run_ctx.tasks[task.name] = TaskState.FAILED
                                        self.trace.on_node_error(task.name, e) # Log it
                                    else:
                                        # fail=stop (default)
                                        run_ctx.status = RunStatus.FAILED
                                        run_ctx.end_time = time.time()
                                        raise e

        finally:
            # Cleanup active run
            if run_ctx.run_id in self.active_runs:
                del self.active_runs[run_ctx.run_id]

        self.trace.on_flow_end(flow.name)
        
        # Update final run status
        if run_ctx.status == RunStatus.RUNNING:
            if failed:
                # Some tasks failed but were isolated
                # Should run be COMPLETED or FAILED?
                # Usually if flow finished (even with partial failures), it's COMPLETED (or PARTIAL_SUCCESS?)
                # For now let's say COMPLETED if it didn't crash.
                run_ctx.status = RunStatus.COMPLETED # Or maybe FAILED if strict?
            else:
                run_ctx.status = RunStatus.COMPLETED
        
        run_ctx.end_time = time.time()
        return ctx

    def _execute_subflow(self, subflow, ctx: Context):
        for node in subflow.steps:
            self._execute_node(node, ctx)

    def _execute_node(self, node, ctx: Context):
        if isinstance(node, TaskNode):
            self._execute_task(node.task, ctx)
        elif isinstance(node, RepeatNode):
            self._execute_repeat(node, ctx)
        elif isinstance(node, ForEachNode):
            self._execute_foreach(node, ctx)
        elif isinstance(node, UntilNode):
            self._execute_until(node, ctx)
        elif isinstance(node, SwitchNode):
            self._execute_switch(node, ctx)
        else:
            raise TypeError(f"Unknown node type: {type(node)}")

    def _execute_repeat(self, node: RepeatNode, ctx: Context):
        count_value = self._resolve_repeat_count(node.count, ctx)
        for index in range(count_value):
            frame = LoopFrame(name="repeat", type="repeat", index=index, iteration=index + 1, count=count_value)
            ctx.push_loop(frame)
            try:
                self._execute_subflow(node.body, ctx)
            finally:
                ctx.pop_loop()

    def _execute_foreach(self, node: ForEachNode, ctx: Context):
        sequence = self._eval_expression(node.source, ctx)
        if not isinstance(sequence, (list, tuple)):
            raise TypeError("ForEach source must evaluate to a list or tuple.")

        total = len(sequence)
        label = node.alias or node.source.source
        for index, item in enumerate(sequence):
            frame = LoopFrame(
                name=f"foreach:{label}",
                type="foreach",
                index=index,
                iteration=index + 1,
                count=total,
                item=item,
            )
            ctx.push_loop(frame)
            if node.alias:
                ctx.set_var(node.alias, item)
            try:
                self._execute_subflow(node.body, ctx)
            finally:
                if node.alias:
                    ctx.clear_var(node.alias)
                ctx.pop_loop()

    def _execute_until(self, node: UntilNode, ctx: Context):
        max_iter = node.max_iter or 1000
        iteration = 0
        last_condition = None
        while True:
            iteration += 1
            frame = LoopFrame(
                name="until",
                type="until",
                index=iteration - 1,
                iteration=iteration,
                condition=last_condition,
                count=max_iter,
            )
            ctx.push_loop(frame)
            try:
                self._execute_subflow(node.body, ctx)
                condition_result = bool(self._eval_expression(node.condition, ctx))
            finally:
                ctx.pop_loop()

            last_condition = condition_result
            if condition_result:
                break
            if iteration >= max_iter:
                raise UntilMaxIterationsExceeded(node.condition.source, max_iter)

    def _execute_switch(self, node: SwitchNode, ctx: Context):
        value = self._eval_expression(node.expression, ctx)
        default_case = None
        for case in node.cases:
            if case.value == DEFAULT_CASE_VALUE:
                if default_case is None:
                    default_case = case
                continue
            if case.value == value:
                self._execute_subflow(case.target, ctx)
                return
        if default_case:
            self._execute_subflow(default_case.target, ctx)
    def _resolve_repeat_count(self, count_value, ctx: Context) -> int:
        if isinstance(count_value, Expression):
            resolved = self._eval_expression(count_value, ctx)
        else:
            resolved = count_value
        if not isinstance(resolved, int):
            raise TypeError("Repeat count must evaluate to an integer.")
        if resolved < 0:
            raise ValueError("Repeat count cannot be negative.")
        return resolved

    def _eval_expression(self, expression, ctx: Context):
        if isinstance(expression, Expression):
            return expression.evaluate(ctx=ctx.expression_data(), env=ctx.env_data())
        return expression

    def _execute_task(self, task: Task, ctx: Context):
        # Update state to RUNNING
        from .models import TaskState
        run_ctx = ctx.run_context
        if ctx.run_context:
            ctx.run_context.tasks[task.name] = TaskState.RUNNING
            record = ctx.run_context.ensure_task_record(task.name)
            record.state = TaskState.RUNNING
            record.started_at = time.time()
            record.error = None
            record.traceback = None
        else:
            record = None

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
                
                if record:
                    record.inputs = {k: v for k, v in kwargs.items() if k != "ctx"}

                stdout_capture = TeeStream(sys.stdout)
                stderr_capture = TeeStream(sys.stderr)
                with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                    result = task.func(**kwargs)
                ctx.set_result(task.name, result)
                if run_ctx:
                    run_ctx.append_log(task.name, "stdout", stdout_capture.getvalue())
                    run_ctx.append_log(task.name, "stderr", stderr_capture.getvalue())
                
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
                
                # Update state to SUCCEEDED
                if ctx.run_context:
                    ctx.run_context.tasks[task.name] = TaskState.SUCCEEDED
                    if record:
                        record.state = TaskState.SUCCEEDED
                        record.ended_at = time.time()
                        record.duration_ms = (record.ended_at - record.started_at) * 1000
                        record.output = result
                
                return # Success
                
            except Exception as e:
                if run_ctx:
                    run_ctx.append_log(task.name, "stdout", stdout_capture.getvalue() if 'stdout_capture' in locals() else "")
                    run_ctx.append_log(task.name, "stderr", stderr_capture.getvalue() if 'stderr_capture' in locals() else "")
                if record:
                    record.state = TaskState.FAILED
                    record.ended_at = time.time()
                    record.duration_ms = (record.ended_at - record.started_at) * 1000
                    record.error = str(e)
                    record.traceback = traceback.format_exc()
                if retries_left > 0:
                    retries_left -= 1
                    # Log retry?
                    # self.trace.on_node_retry(task.name, e, retries_left) # If method exists
                    # For now just continue
                    time.sleep(0.1) # Small backoff?
                    continue
                else:
                    self.trace.on_node_error(task.name, e)
                    # Update state to FAILED
                    if ctx.run_context:
                        ctx.run_context.tasks[task.name] = TaskState.FAILED
                    raise e
