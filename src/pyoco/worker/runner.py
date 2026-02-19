import time
import uuid
from typing import List, Optional
from ..core.engine import Engine
from ..core.models import RunContext, RunStatus
from ..trace.backend import TraceBackend
from ..discovery.loader import TaskLoader
from ..schemas.config import PyocoConfig
from ..client import Client
from ..dsl.graph import build_flow_from_graph

from ..trace.console import ConsoleTraceBackend

class RemoteTraceBackend(TraceBackend):
    def __init__(self, client: Client, run_ctx: RunContext, cute: bool = True):
        self.client = client
        self.run_ctx = run_ctx
        self.last_heartbeat = 0
        self.heartbeat_interval = 1.0 # sec
        self.console = ConsoleTraceBackend(style="cute" if cute else "plain")

    def _send_heartbeat(self, force=False):
        now = time.time()
        if force or (now - self.last_heartbeat > self.heartbeat_interval):
            cancel = self.client.heartbeat(self.run_ctx)
            if cancel and self.run_ctx.status not in [RunStatus.CANCELLING, RunStatus.CANCELLED]:
                print(f"🛑 Cancellation requested from server for run {self.run_ctx.run_id}")
                self.run_ctx.status = RunStatus.CANCELLING
            self.last_heartbeat = now

    def on_flow_start(self, name: str, run_id: Optional[str] = None):
        self.console.on_flow_start(name, run_id)
        self._send_heartbeat(force=True)

    def on_flow_end(self, name: str):
        self.console.on_flow_end(name)
        self._send_heartbeat(force=True)

    def on_node_start(self, node_name: str):
        self.console.on_node_start(node_name)
        self._send_heartbeat()

    def on_node_end(self, node_name: str, duration: float):
        self.console.on_node_end(node_name, duration)
        self._send_heartbeat(force=True)

    def on_node_error(self, node_name: str, error: Exception):
        self.console.on_node_error(node_name, error)
        self._send_heartbeat(force=True)


class Worker:
    def __init__(self, server_url: str, config: PyocoConfig, tags: List[str] = []):
        self.server_url = server_url
        self.config = config
        self.tags = tags
        self.worker_id = f"w-{uuid.uuid4().hex[:8]}"
        self.client = Client(server_url, self.worker_id)
        self.loader = TaskLoader(config)
        self.loader.load() # Load tasks/flows once

    def start(self):
        print(f"🐜 Worker {self.worker_id} started. Connected to {self.server_url}")
        try:
            while True:
                job = self.client.poll(self.tags)
                if job:
                    self._execute_job(job)
                else:
                    time.sleep(2.0)
        except KeyboardInterrupt:
            print("\n🛑 Worker stopping...")

    def _execute_job(self, job):
        run_id = job["run_id"]
        flow_name = job["flow_name"]
        params = job["params"] or {}
        
        print(f"🚀 Received job: {run_id} (Flow: {flow_name})")
        
        flow_def = self.config.flow
        if not flow_def:
            print("❌ Flow not found in local config. Add 'flow:' with 'graph:' to your flow.yaml.")
            return

        try:
            flow = build_flow_from_graph(
                graph=flow_def.graph,
                tasks=self.loader.tasks,
                pipes=self.config.pipes,
                flow_name=flow_name,
            )
        except Exception as e:
            print(f"❌ Error building flow: {e}")
            return
        
        # Execute
        engine = Engine()

        run_ctx = RunContext(run_id=run_id, status=RunStatus.RUNNING)
        backend = RemoteTraceBackend(self.client, run_ctx)
        engine.trace = backend
        
        try:
            engine.run(flow, params=params, run_context=run_ctx)
            print(f"✅ Job {run_id} completed: {run_ctx.status}")
            # Send final heartbeat
            self.client.heartbeat(run_ctx)
        except Exception as e:
            print(f"💥 Job {run_id} failed: {e}")
            # Heartbeat one last time
            run_ctx.status = RunStatus.FAILED
            self.client.heartbeat(run_ctx)
