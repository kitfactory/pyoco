from typing import Any, Callable, Dict, List, Optional, Set, Union, ForwardRef
from dataclasses import dataclass, field

@dataclass
class Task:
    func: Callable
    name: str
    dependencies: Set['Task'] = field(default_factory=set)
    dependents: Set['Task'] = field(default_factory=set)
    # Inputs configuration from flow.yaml
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list) # list of context paths to save result to
    # For parallel execution grouping
    parallel_group: Optional[str] = None 
    
    # Failure handling
    fail_policy: str = "stop" # stop, isolate, retry
    retries: int = 0
    timeout_sec: Optional[float] = None
    
    # Trigger policy
    trigger_policy: str = "ALL" # ALL (AND-join), ANY (OR-join)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Task):
            return self.name == other.name
        return False

    def __repr__(self):
        return f"<Task {self.name}>"

@dataclass
class Flow:
    name: str = "main"
    tasks: Set[Task] = field(default_factory=set)
    _tail: Set[Task] = field(default_factory=set)
    
    def __rshift__(self, other):
        # Flow >> Task/List/Branch
        new_tasks = []
        is_branch = False
        
        # Check if we are connecting FROM a Branch?
        # No, Flow >> X means we are adding X to the flow, and connecting current tail to X.
        # If X is a Branch (A | B), it means we add A and B, and tail connects to both.
        # But wait, the OR logic applies when (A | B) >> C.
        # Here we are just building the graph.
        # If we do Flow >> (A | B) >> C
        # 1. Flow >> (A | B) -> Adds A, B. Tail = {A, B}.
        # 2. (Flow... which returns Flow) >> C -> Tail {A, B} >> C.
        # Here C depends on A AND B by default.
        # We need to detect if the tail came from a Branch?
        # But Flow._tail is just a set of tasks.
        # We need to know if those tasks were added as a Branch.
        # This is tricky with the current Flow implementation which just tracks tail tasks.
        # However, the syntax (A | B) returns a Branch object.
        # If we do:
        # branch = (A | B)
        # branch >> C
        # We need to handle this in Branch.__rshift__ or TaskWrapper.__rshift__?
        # Wait, (A | B) returns a Branch (list subclass).
        # Python's list doesn't have __rshift__.
        # We need Branch to implement __rshift__.
        
        if hasattr(other, 'task'): # TaskWrapper
            new_tasks = [other.task]
        elif isinstance(other, Task):
            new_tasks = [other]
        elif isinstance(other, (list, tuple)):
            # Check if it's a Branch
            from ..dsl.syntax import Branch # Import here to avoid circular import if possible, or move Branch to models?
            # Actually Branch is defined in syntax.py, but Flow is in models.py.
            # We can't import syntax in models easily.
            # Maybe check class name?
            if type(other).__name__ == "Branch":
                is_branch = True
                
            for item in other:
                if hasattr(item, 'task'):
                    new_tasks.append(item.task)
                elif isinstance(item, Task):
                    new_tasks.append(item)
        
        # Add tasks and link from current tail
        for t in new_tasks:
            self.add_task(t)
            for tail_task in self._tail:
                tail_task.dependents.add(t)
                t.dependencies.add(tail_task)
            
            # If the tail was a Branch, does it mean t should be ANY?
            # No, Flow tracks tail. If we want (A | B) >> C to mean C waits for ANY,
            # we need to know that A and B are "OR-grouped".
            # But Flow just sees A and B in tail.
            # If we want to support this, we might need to change how we link.
            # OR, we rely on the fact that the USER does:
            # (A | B) >> C
            # This calls Branch.__rshift__(C).
            # So we need to implement Branch.__rshift__.
            # Flow.__rshift__ is only used when we do `flow >> ...`.
            # So `flow >> (A | B)` just adds A and B.
            # Then `(A | B) >> C` is handled by Branch.
            pass
        
        # Update tail
        if new_tasks:
            self._tail = set(new_tasks)
            
        return self

    def add_task(self, task: Task):
        self.tasks.add(task)

