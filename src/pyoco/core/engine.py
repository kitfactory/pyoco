import time
from typing import Dict, Any, List, Set
from .models import Flow, Task
from .context import Context
from ..trace.backend import TraceBackend
from ..trace.console import ConsoleTraceBackend

class Engine:
    def __init__(self, trace_backend: TraceBackend = None):
        self.trace = trace_backend or ConsoleTraceBackend()

    def run(self, flow: Flow, params: Dict[str, Any] = None) -> Context:
        ctx = Context(params=params or {})
        self.trace.on_flow_start(flow.name)
        
        # Topological sort or just simple execution for now
        # The spec mentions "DAG analysis + dependency resolution node parallel execution"
        # For MVP, we can do a simple topological sort and sequential execution, 
        # or a loop that finds runnable tasks.
        
        executed: Set[Task] = set()
        
        # Simple loop for execution
        while len(executed) < len(flow.tasks):
            runnable = []
            for task in flow.tasks:
                if task in executed:
                    continue
                
                # Check dependencies
                deps_met = True
                for dep in task.dependencies:
                    if dep not in executed:
                        deps_met = False
                        break
                
                if deps_met:
                    runnable.append(task)
            
            if not runnable:
                # Deadlock or cycle
                raise RuntimeError("Deadlock or cycle detected in workflow")
            
            # Execute runnable tasks (sequentially for now, but could be parallel)
            for task in runnable:
                self._execute_task(task, ctx)
                executed.add(task)
                
        self.trace.on_flow_end(flow.name)
        return ctx

    def _execute_task(self, task: Task, ctx: Context):
        self.trace.on_node_start(task.name)
        start_time = time.time()
        try:
            # Resolve inputs
            # The spec says: inputs: x: $node.A.output
            # But for the Python API: def A(ctx, x:int)
            # We need to inject arguments.
            # For MVP Python API, we pass ctx and maybe params?
            # The spec example: def A(ctx, x:int)->int: return x+1
            # And run(flow, params={"x":1})
            # So we need to resolve 'x' from params or previous results.
            
            # Simple injection logic:
            # 1. Pass ctx as first arg if typed/named 'ctx'
            # 2. Resolve other args from params or ctx.results
            
            kwargs = {}
            # Inspect function signature (omitted for brevity, assuming simple kwargs match)
            # For now, let's just pass ctx and params merged with results
            
            # MERGE params and results for simple resolution
            # This is a simplification. Real implementation needs signature inspection.
            
            # If the function expects 'ctx', pass it.
            # If it expects 'x', look in params, then results.
            
            import inspect
            sig = inspect.signature(task.func)
            for param_name, param in sig.parameters.items():
                if param_name == 'ctx':
                    kwargs['ctx'] = ctx
                elif param_name in ctx.params:
                    kwargs[param_name] = ctx.params[param_name]
                elif param_name in ctx.results:
                    kwargs[param_name] = ctx.results[param_name]
                # Handle implicit inputs from dependencies if needed
            
            result = task.func(**kwargs)
            ctx.results[task.name] = result
            
            duration = (time.time() - start_time) * 1000
            self.trace.on_node_end(task.name, duration)
            
        except Exception as e:
            self.trace.on_node_error(task.name, e)
            raise e
