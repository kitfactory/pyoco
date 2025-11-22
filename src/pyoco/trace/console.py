import time
from .backend import TraceBackend

class ConsoleTraceBackend(TraceBackend):
    def __init__(self, style: str = None):
        if style is None:
            import os
            env_cute = os.environ.get("PYOCO_CUTE", "true").lower()
            if env_cute in ["0", "false", "no", "off"]:
                style = "plain"
            else:
                style = "cute"
        self.style = style

    def on_flow_start(self, flow_name: str, run_id: str = None):
        rid_str = f" run_id={run_id}" if run_id else ""
        if self.style == "cute":
            print(f"🐇 pyoco > start flow={flow_name}{rid_str}")
        else:
            print(f"INFO pyoco start flow={flow_name}{rid_str}")

    def on_flow_end(self, flow_name: str):
        if self.style == "cute":
            print(f"🥕 done flow={flow_name}")
        else:
            print(f"INFO pyoco end flow={flow_name}")

    def on_node_start(self, node_name: str):
        if self.style == "cute":
            print(f"🏃 start node={node_name}")
        else:
            print(f"INFO pyoco start node={node_name}")

    def on_node_end(self, node_name: str, duration_ms: float):
        if self.style == "cute":
            print(f"✅ done node={node_name} ({duration_ms:.2f} ms)")
        else:
            print(f"INFO pyoco end node={node_name} dur_ms={duration_ms:.2f}")

    def on_node_error(self, node_name: str, error: Exception):
        if self.style == "cute":
            print(f"💥 error node={node_name} {error}")
        else:
            print(f"ERROR pyoco error node={node_name} {error}")

    def on_node_transition(self, source: str, target: str):
        if self.style == "cute":
            print(f"🐇 {source} -> {target}")
