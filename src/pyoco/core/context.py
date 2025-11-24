import threading
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, field
from .models import RunContext


@dataclass
class LoopFrame:
    name: str
    type: str
    index: Optional[int] = None
    iteration: Optional[int] = None
    count: Optional[int] = None
    item: Any = None
    condition: Optional[bool] = None
    path: Optional[str] = None


class LoopStack:
    def __init__(self):
        self._frames: List[LoopFrame] = []

    def push(self, frame: LoopFrame) -> LoopFrame:
        parent_path = self._frames[-1].path if self._frames else ""
        segment = frame.name
        if frame.index is not None:
            segment = f"{segment}[{frame.index}]"
        frame.path = f"{parent_path}.{segment}" if parent_path else segment
        self._frames.append(frame)
        return frame

    def pop(self) -> LoopFrame:
        if not self._frames:
            raise RuntimeError("Loop stack underflow")
        return self._frames.pop()

    @property
    def current(self) -> Optional[LoopFrame]:
        return self._frames[-1] if self._frames else None

    def snapshot(self) -> Sequence[LoopFrame]:
        return tuple(self._frames)

@dataclass
class Context:
    """
    Execution context passed to tasks.
    """
    params: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    scratch: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    env: Dict[str, str] = field(default_factory=dict)
    artifact_dir: Optional[str] = None
    _vars: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Reference to the parent run context (v0.2.0+)
    run_context: Optional[RunContext] = None
    
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _loop_stack: LoopStack = field(default_factory=LoopStack, repr=False)

    @property
    def is_cancelled(self) -> bool:
        if self.run_context:
            from .models import RunStatus
            return self.run_context.status in [RunStatus.CANCELLING, RunStatus.CANCELLED]
        return False

    @property
    def loop(self) -> Optional[LoopFrame]:
        return self._loop_stack.current

    @property
    def loops(self) -> Sequence[LoopFrame]:
        return self._loop_stack.snapshot()

    def push_loop(self, frame: LoopFrame) -> LoopFrame:
        return self._loop_stack.push(frame)

    def pop_loop(self) -> LoopFrame:
        return self._loop_stack.pop()

    def set_var(self, name: str, value: Any):
        self._vars[name] = value

    def get_var(self, name: str, default=None):
        return self._vars.get(name, default)

    def clear_var(self, name: str):
        self._vars.pop(name, None)

    def __post_init__(self):
        # Ensure artifact directory exists
        if self.artifact_dir is None:
            self.artifact_dir = "./artifacts"
            
        import pathlib
        pathlib.Path(self.artifact_dir).mkdir(parents=True, exist_ok=True)

    def get_result(self, node_name: str) -> Any:
        with self._lock:
            return self.results.get(node_name)
            
    def set_result(self, node_name: str, value: Any):
        with self._lock:
            self.results[node_name] = value
            
    def save_artifact(self, name: str, data: Any) -> str:
        import os
        import pathlib
        
        full_path = pathlib.Path(self.artifact_dir) / name
        # Ensure parent dir exists for nested artifacts
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "w"
        content = data
        
        if isinstance(data, bytes):
            mode = "wb"
        elif not isinstance(data, str):
            content = str(data)
            
        with open(full_path, mode) as f:
            f.write(content)
            
        abs_path = str(full_path.absolute())
        
        type_name = type(data).__name__
        if isinstance(data, (dict, list)):
            type_name = "object"
            
        with self._lock:
            self.artifacts[name] = {
                "path": abs_path,
                "type": type_name
            }
            
        return abs_path

    def resolve(self, value: Any) -> Any:
        if not isinstance(value, str) or not value.startswith("$"):
            return value
        
        # $node.<Name>.output
        if value.startswith("$node."):
            parts = value.split(".")
            # $node.A.output -> ["$node", "A", "output"]
            # $node.A.output.x -> ["$node", "A", "output", "x"]
            if len(parts) < 3 or parts[2] != "output":
                 # Malformed or unsupported node selector
                 return value
            
            node_name = parts[1]
            if node_name not in self.results:
                raise KeyError(f"Node '{node_name}' result not found in context.")
            
            result = self.results[node_name]
            
            # Handle nested access
            if len(parts) > 3:
                for key in parts[3:]:
                    if isinstance(result, dict):
                        result = result[key]
                    else:
                        result = getattr(result, key)
            return result

        # $ctx.params.<Key>
        if value.startswith("$ctx.params."):
            key = value[len("$ctx.params."):]
            if key not in self.params:
                raise KeyError(f"Param '{key}' not found in context.")
            return self.params[key]

        # $env.<Key>
        if value.startswith("$env."):
            import os
            key = value[len("$env."):]
            # Check ctx.env first, then os.environ
            if key in self.env:
                return self.env[key]
            if key in os.environ:
                return os.environ[key]
            raise KeyError(f"Environment variable '{key}' not found.")

        return value

    def expression_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data.update(self._vars)
        data["params"] = self.params
        data["results"] = self.results
        data["scratch"] = self.scratch
        data["artifacts"] = self.artifacts
        data["loop"] = self.loop
        data["loops"] = list(self.loops)
        return data

    def env_data(self) -> Dict[str, str]:
        import os

        env_data = dict(os.environ)
        env_data.update(self.env)
        return env_data
