import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Context:
    params: Dict[str, Any] = field(default_factory=dict)
    env: Dict[str, str] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    scratch: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    run_id: Optional[str] = None
    artifact_dir: str = field(default="./artifacts")
    
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        # Ensure artifact directory exists
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

