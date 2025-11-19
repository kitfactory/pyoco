from abc import ABC, abstractmethod
from typing import Any, Optional

class TraceBackend(ABC):
    @abstractmethod
    def on_flow_start(self, flow_name: str):
        pass

    @abstractmethod
    def on_flow_end(self, flow_name: str):
        pass

    @abstractmethod
    def on_node_start(self, node_name: str):
        pass

    @abstractmethod
    def on_node_end(self, node_name: str, duration_ms: float):
        pass

    @abstractmethod
    def on_node_error(self, node_name: str, error: Exception):
        pass
