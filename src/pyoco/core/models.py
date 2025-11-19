from typing import Any, Callable, Dict, List, Optional, Set, Union, ForwardRef
from dataclasses import dataclass, field

@dataclass
class Task:
    func: Callable
    name: str
    dependencies: Set['Task'] = field(default_factory=set)
    dependents: Set['Task'] = field(default_factory=set)
    # For parallel execution grouping
    parallel_group: Optional[str] = None 

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"<Task {self.name}>"

@dataclass
class Flow:
    name: str = "main"
    tasks: Set[Task] = field(default_factory=set)
    _tail: Set[Task] = field(default_factory=set)
    
    def __rshift__(self, other):
        # Flow >> Task/List
        new_tasks = []
        
        if hasattr(other, 'task'): # TaskWrapper
            new_tasks = [other.task]
        elif isinstance(other, Task):
            new_tasks = [other]
        elif isinstance(other, (list, tuple)):
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
        
        # Update tail
        if new_tasks:
            self._tail = set(new_tasks)
            
        return self

    def add_task(self, task: Task):
        self.tasks.add(task)

