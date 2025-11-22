import time
import uuid
from typing import List, Optional
from ..core.engine import Engine
from ..core.models import RunContext, RunStatus, Flow
from ..trace.backend import TraceBackend
from ..discovery.loader import TaskLoader
from ..schemas.config import PyocoConfig
from ..client import Client

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
            cancel = self.client.heartbeat(
                self.run_ctx.run_id,
                self.run_ctx.tasks,
                self.run_ctx.status
            )
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
        
        # Find flow
        flow_def = self.config.flows.get(flow_name)
        if not flow_def:
            print(f"❌ Flow '{flow_name}' not found in local config.")
            return

        # Build Flow object using exec (same as main.py)
        from ..core.models import Flow as FlowModel
        from ..dsl.syntax import TaskWrapper
        
        eval_context = {name: TaskWrapper(task) for name, task in self.loader.tasks.items()}
        
        try:
            flow = FlowModel(name=flow_name)
            for t in self.loader.tasks.values():
                flow.add_task(t)
            
            # Evaluate graph
            exec(flow_def.graph, {}, eval_context)
            
        except Exception as e:
            print(f"❌ Error building flow: {e}")
            return
        
        # Execute
        engine = Engine()
        
        # We need to inject run_id into Engine.
        # Engine.run generates run_id if not provided.
        # We need to pass it.
        # Engine.run doesn't accept run_id argument currently.
        # It creates RunContext inside.
        # I need to modify Engine.run to accept optional run_id or RunContext.
        
        # Wait, I modified Engine.run in v0.2.0.
        # Let's check Engine.run signature.
        pass 
        
        # I will modify Engine.run to accept run_id.
        # For now, let's assume I will do that.
        
        # Create RemoteTraceBackend
        # But we need run_ctx to create backend.
        # And Engine creates run_ctx.
        # Chicken and egg.
        
        # Solution: Engine.run should accept an existing RunContext or run_id.
        # If I pass run_id, Engine creates RunContext with that ID.
        # Then I can access it?
        # Or I pass a callback to get it?
        
        # Better: Pass run_id to Engine.run.
        # Engine creates RunContext.
        # Engine calls trace.on_flow_start(run_id=...).
        # RemoteTraceBackend receives run_id.
        # But RemoteTraceBackend needs to know which run_id to report to (it knows from constructor).
        # Actually, RemoteTraceBackend needs access to the RunContext object that Engine creates.
        # Because it reads `run_ctx.tasks` and `run_ctx.status`.
        
        # If Engine creates RunContext internally, we can't pass it to Backend beforehand.
        # Unless Engine exposes it.
        
        # Alternative:
        # Modify Engine to accept `run_context` argument.
        # If provided, use it.
        
        # I will modify Engine.run to accept `run_context`.
        
        run_ctx = RunContext(run_id=run_id, status=RunStatus.RUNNING)
        # Initialize tasks as PENDING? Engine does that.
        
        backend = RemoteTraceBackend(self.client, run_ctx)
        engine.trace = backend # Replace default console trace? Or chain?
        # Maybe chain if we want local logs too.
        # For now, just replace or use MultiBackend (not implemented).
        # Let's just use RemoteBackend.
        
        try:
            engine.run(flow, params=params, run_context=run_ctx)
            print(f"✅ Job {run_id} completed: {run_ctx.status}")
            # Send final heartbeat
            self.client.heartbeat(run_id, run_ctx.tasks, run_ctx.status)
        except Exception as e:
            print(f"💥 Job {run_id} failed: {e}")
            # Heartbeat one last time
            run_ctx.status = RunStatus.FAILED
            self.client.heartbeat(run_id, run_ctx.tasks, run_ctx.status)

