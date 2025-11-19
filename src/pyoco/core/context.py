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

    def get_result(self, node_name: str) -> Any:
        return self.results.get(node_name)
