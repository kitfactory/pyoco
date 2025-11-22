from typing import Callable, Union, List, Tuple
from ..core.models import Task, Flow
from ..core import engine

# Global context
_active_flow: Flow = None

def task(func: Callable) -> Task:
    t = Task(func=func, name=func.__name__)
    return t

class Branch(list):
    """Represents a branch of tasks (OR-split/join logic placeholder)."""
    def __rshift__(self, other):
        # (A | B) >> C
        # C depends on A and B.
        # AND C.trigger_policy = "ANY"
        
        targets = []
        if hasattr(other, 'task'):
            targets = [other.task]
        elif isinstance(other, (list, tuple)):
             for item in other:
                if hasattr(item, 'task'):
                    targets.append(item.task)
        
        for target in targets:
            target.trigger_policy = "ANY"
            for source in self:
                if hasattr(source, 'task'):
                    target.dependencies.add(source.task)
                    source.task.dependents.add(target)
        
        return other

class Parallel(list):
    """Represents a parallel group of tasks (AND-split/join)."""
    def __rshift__(self, other):
        # (A & B) >> C
        # C depends on A AND B.
        
        targets = []
        if hasattr(other, 'task'):
            targets = [other.task]
        elif isinstance(other, (list, tuple)):
             for item in other:
                if hasattr(item, 'task'):
                    targets.append(item.task)
        
        for target in targets:
            for source in self:
                if hasattr(source, 'task'):
                    target.dependencies.add(source.task)
                    source.task.dependents.add(target)
        
        return other

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
            # self >> (A & B) or self >> (A | B)
            # If it's a Branch (from |), does it imply something different?
            # Spec says: "Update Flow to handle Branch >> Task (set trigger_policy=ANY)"
            # But here we are doing Task >> Branch.
            # Task >> (A | B) means Task triggers both A and B?
            # Usually >> means "follows".
            # A >> (B | C) -> A triggers B and C?
            # Or does it mean B and C depend on A? Yes.
            # The difference between & and | is usually how they JOIN later, or how they are triggered?
            # In Airflow, >> [A, B] means A and B depend on upstream.
            # If we have (A | B) >> C, then C depends on A OR B.
            # So if 'other' is a Branch, we just add dependencies as usual.
            # The "OR" logic is relevant when 'other' connects to downstream.
            
            for item in other:
                if isinstance(item, TaskWrapper):
                    item.task.dependencies.add(self.task)
                    self.task.dependents.add(item.task)
            return other
        return other

    def __and__(self, other):
        # self & other (Parallel)
        return Parallel([self, other])

    def __or__(self, other):
        # self | other (Branch)
        # Return a Branch object containing both
        return Branch([self, other])

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
