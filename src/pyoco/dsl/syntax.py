from typing import Callable, Union, List, Tuple
from ..core.models import Task, Flow
from ..core import engine

# Global context
_active_flow: Flow = None

def task(func: Callable) -> Task:
    t = Task(func=func, name=func.__name__)
    return t

class TaskWrapper:
    """
    Wraps a Task to handle DSL operators and registration.
    """
    def __init__(self, task: Task):
        self.task = task
    
    def __call__(self, *args, **kwargs):
        # In this new spec, calling a task might not be strictly necessary for registration
        # if we assume tasks are added to flow explicitly or via >>
        # But let's keep the pattern: calling it returns a wrapper that can be chained
        # We might need to store args/kwargs if we want to support them
        return self

    def __rshift__(self, other):
        # self >> other
        if isinstance(other, TaskWrapper):
            other.task.dependencies.add(self.task)
            self.task.dependents.add(other.task)
            return other
        elif isinstance(other, (list, tuple)):
            # self >> (A & B)
            for item in other:
                if isinstance(item, TaskWrapper):
                    item.task.dependencies.add(self.task)
                    self.task.dependents.add(item.task)
            return other
        return other

    def __and__(self, other):
        # self & other (Parallel)
        return [self, other]

    def __or__(self, other):
        # self | other (Branch - not fully defined in spec logic, but syntax-wise)
        return [self, other]

# We need to adapt the DSL to match the spec:
# @task
# def A(ctx, x:int)->int: ...
# flow = Flow() >> A >> (B & C)

# So A, B, C must be usable in the expression.
# The @task decorator should return something that supports >>, &, |

def task_decorator(func: Callable):
    t = Task(func=func, name=func.__name__)
    return TaskWrapper(t)

# Re-export as task
task = task_decorator
