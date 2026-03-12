from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import yaml

@dataclass
class TaskConfig:
    callable: Optional[str] = None
    use: Optional[str] = None
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
    pipes: Dict[str, str] = field(default_factory=dict)
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

        tasks: Dict[str, TaskConfig] = {}
        for name, value in data.get("tasks", {}).items():
            if not isinstance(value, dict):
                raise ValueError(f"Invalid config: tasks.{name} must be a mapping/object.")
            task_conf = TaskConfig(**value)
            if task_conf.callable and task_conf.use:
                raise ValueError(
                    f"Invalid config: tasks.{name} cannot define both 'callable' and 'use'."
                )
            tasks[name] = task_conf
        pipes_data = data.get("pipes", {}) or {}
        if not isinstance(pipes_data, dict):
            raise ValueError("Invalid config: 'pipes' must be a mapping/object.")
        pipes: Dict[str, str] = {}
        for name, value in pipes_data.items():
            if not isinstance(value, str):
                raise ValueError(f"Invalid config: pipes.{name} must be a string.")
            pipes[name] = value

        if "discovery" in data:
            raise ValueError(
                "Unsupported config key 'discovery'.\n"
                "For safety, discovery scope is not configurable in flow.yaml.\n"
                "Remove 'discovery' and use PYOCO_DISCOVERY_MODULES to import extra modules, "
                "or define tasks via tasks.<name>.use / tasks.<name>.callable."
            )

        run_data = data.get('runtime', {})
        runtime = RuntimeConfig(**run_data)
        
        return cls(
            version=data.get('version', 1),
            flow=flow,
            tasks=tasks,
            pipes=pipes,
            runtime=runtime
        )
