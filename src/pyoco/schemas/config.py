from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import yaml

@dataclass
class TaskConfig:
    callable: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)

@dataclass
class FlowConfig:
    graph: str
    defaults: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeConfig:
    expose_env: List[str] = field(default_factory=list)

@dataclass
class PyocoConfig:
    version: int
    flow: Optional[FlowConfig]
    tasks: Dict[str, TaskConfig]
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    @classmethod
    def from_yaml(cls, path: str) -> 'PyocoConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Simple manual parsing/validation for MVP
        # In a real app, use pydantic or similar

        if "flows" in data:
            raise ValueError(
                "Unsupported config key 'flows'.\n"
                "Pyoco config supports a single workflow per file.\n"
                "Use 'flow:' instead.\n"
                "Example:\n"
                "  flow:\n"
                "    graph: |\n"
                "      task_a >> task_b\n"
            )

        flow_data = data.get("flow")
        flow = None
        if flow_data is not None:
            if not isinstance(flow_data, dict):
                raise ValueError("Invalid config: 'flow' must be a mapping/object.")
            flow = FlowConfig(**flow_data)

        tasks = {k: TaskConfig(**v) for k, v in data.get('tasks', {}).items()}

        if "discovery" in data:
            raise ValueError(
                "Unsupported config key 'discovery'.\n"
                "For safety, discovery scope is not configurable in flow.yaml.\n"
                "Remove 'discovery' and use PYOCO_DISCOVERY_MODULES to import extra modules, "
                "or define tasks explicitly via tasks.<name>.callable."
            )

        run_data = data.get('runtime', {})
        runtime = RuntimeConfig(**run_data)
        
        return cls(
            version=data.get('version', 1),
            flow=flow,
            tasks=tasks,
            runtime=runtime
        )
