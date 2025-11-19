from .core.models import Flow, Task
from .core.engine import Engine
from .dsl.syntax import task
from .trace.console import ConsoleTraceBackend

def run(flow: Flow, params: dict = None, trace: bool = True, cute: bool = True):
    backend = ConsoleTraceBackend(style="cute" if cute else "plain")
    engine = Engine(trace_backend=backend)
    return engine.run(flow, params)

__all__ = ["task", "Flow", "run"]
