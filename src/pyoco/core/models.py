from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
import json

@dataclass
class Task:
    """
    Represents a single unit of work in the workflow.
    
    Designed to be lightweight and serializable.
    Contains metadata about the task, its dependencies, and execution policies.
    """
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

class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class RunStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"

@dataclass
class TaskRecord:
    state: TaskState = TaskState.PENDING
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    output: Any = None
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunContext:
    """
    Holds the state of a single workflow execution.
    """
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    flow_name: str = "main"
    params: Dict[str, Any] = field(default_factory=dict)
    status: RunStatus = RunStatus.RUNNING
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    task_records: Dict[str, TaskRecord] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    _pending_logs: List[Dict[str, Any]] = field(default_factory=list, repr=False)
    _log_seq: int = field(default=0, repr=False)
    log_bytes: Dict[str, int] = field(default_factory=dict)
    metrics_recorded_tasks: Set[str] = field(default_factory=set, repr=False)
    metrics_run_observed: bool = field(default=False, repr=False)
    webhook_notified_status: Optional[str] = field(default=None, repr=False)

    def ensure_task_record(self, task_name: str) -> TaskRecord:
        if task_name not in self.task_records:
            self.task_records[task_name] = TaskRecord()
        return self.task_records[task_name]

    def append_log(self, task_name: str, stream: str, payload: str):
        if not payload:
            return
        entry = {
            "seq": self._log_seq,
            "task": task_name,
            "stream": stream,
            "text": payload,
            "timestamp": time.time(),
        }
        self._log_seq += 1
        self.logs.append(entry)
        self._pending_logs.append(entry)

    def drain_logs(self) -> List[Dict[str, Any]]:
        drained = list(self._pending_logs)
        self._pending_logs.clear()
        return drained

    def serialize_task_records(self) -> Dict[str, Any]:
        serialized: Dict[str, Any] = {}
        for name, record in self.task_records.items():
            serialized[name] = {
                "state": record.state.value if hasattr(record.state, "value") else record.state,
                "started_at": record.started_at,
                "ended_at": record.ended_at,
                "duration_ms": record.duration_ms,
                "error": record.error,
                "traceback": record.traceback,
                "inputs": {k: self._safe_value(v) for k, v in record.inputs.items()},
                "output": self._safe_value(record.output),
                "artifacts": record.artifacts,
            }
        return serialized

    def _safe_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        try:
            json.dumps(value)
            return value
        except Exception:
            return repr(value)

@dataclass
class Flow:
    """
    Represents a Directed Acyclic Graph (DAG) of tasks.
    
    Manages the collection of tasks and their dependencies.
    Optimized for single-machine execution without complex scheduling overhead.
    """
    name: str = "main"
    tasks: Set[Task] = field(default_factory=set)
    _tail: Set[Task] = field(default_factory=set)
    _definition: List[Any] = field(default_factory=list, repr=False)
    _has_control_flow: bool = False
    
    def __rshift__(self, other):
        from ..dsl.syntax import TaskWrapper, FlowFragment, ensure_fragment

        if isinstance(other, TaskWrapper):
            fragment = other
            self._record_fragment(fragment)
            self._append_task(fragment.task)
            return self

        if hasattr(other, "to_subflow"):
            fragment = other if isinstance(other, FlowFragment) else ensure_fragment(other)
            self._record_fragment(fragment)
            if not self._has_control_flow and not fragment.has_control_flow():
                self._append_linear_fragment(fragment)
            else:
                self._has_control_flow = True
            return self

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

    def has_control_flow(self) -> bool:
        return self._has_control_flow

    def build_program(self):
        from ..dsl.nodes import SubFlowNode
        return SubFlowNode(list(self._definition))

    def _record_fragment(self, fragment):
        from ..dsl.nodes import TaskNode
        subflow = fragment.to_subflow()
        self._definition.extend(subflow.steps)
        for task in fragment.task_nodes():
            self.add_task(task)
        if any(not isinstance(step, TaskNode) for step in subflow.steps):
            self._has_control_flow = True

    def _append_linear_fragment(self, fragment):
        subflow = fragment.to_subflow()
        for step in subflow.steps:
            if hasattr(step, "task"):
                self._append_task(step.task)

    def _append_task(self, task: Task):
        self.add_task(task)
        if self._has_control_flow:
            self._tail = {task}
            return

        if not self._tail:
            self._tail = {task}
            return

        for tail_task in self._tail:
            tail_task.dependents.add(task)
            task.dependencies.add(tail_task)
        self._tail = {task}
