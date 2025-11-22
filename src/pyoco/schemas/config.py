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
class DiscoveryConfig:
    entry_points: List[str] = field(default_factory=list)
    packages: List[str] = field(default_factory=list)
    glob_modules: List[str] = field(default_factory=list)

@dataclass
class RuntimeConfig:
    expose_env: List[str] = field(default_factory=list)

@dataclass
class PyocoConfig:
    version: int
    flows: Dict[str, FlowConfig]
    tasks: Dict[str, TaskConfig]
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    @classmethod
    def from_yaml(cls, path: str) -> 'PyocoConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Simple manual parsing/validation for MVP
        # In a real app, use pydantic or similar
        
        flows = {k: FlowConfig(**v) for k, v in data.get('flows', {}).items()}
        tasks = {k: TaskConfig(**v) for k, v in data.get('tasks', {}).items()}
        
        disc_data = data.get('discovery', {})
        discovery = DiscoveryConfig(**disc_data)
        
        run_data = data.get('runtime', {})
        runtime = RuntimeConfig(**run_data)
        
        return cls(
            version=data.get('version', 1),
            flows=flows,
            tasks=tasks,
            discovery=discovery,
            runtime=runtime
        )
