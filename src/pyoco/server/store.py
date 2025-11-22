import uuid
import time
from typing import Dict, List, Optional
from ..core.models import RunContext, RunStatus

class StateStore:
    def __init__(self):
        self.runs: Dict[str, RunContext] = {}
        self.queue: List[str] = []
        
    def create_run(self, flow_name: str, params: Dict) -> RunContext:
        run_id = str(uuid.uuid4())
        run_ctx = RunContext(
            run_id=run_id,
            status=RunStatus.PENDING,
            start_time=time.time()
        )
        # Store extra metadata if needed (flow_name, params)
        # For now, RunContext doesn't have flow_name/params fields in core.models.
        # We might need to extend RunContext or store them separately.
        # Let's attach them dynamically for now or assume the worker knows.
        # Actually, the worker needs flow_name and params to run.
        # We should store them in the store alongside the context.
        run_ctx.flow_name = flow_name
        run_ctx.params = params
        
        self.runs[run_id] = run_ctx
        self.queue.append(run_id)
        return run_ctx

    def get_run(self, run_id: str) -> Optional[RunContext]:
        return self.runs.get(run_id)

    def list_runs(self) -> List[RunContext]:
        return list(self.runs.values())

    def dequeue(self, tags: List[str] = None) -> Optional[RunContext]:
        # Simple FIFO queue for now. Tags ignored in v0.3.0 MVP.
        if not self.queue:
            return None
            
        # Find first PENDING run
        # Note: queue might contain cancelled runs?
        # We should check status.
        
        # Pop from front
        # We iterate to find a valid candidate
        for i, run_id in enumerate(self.queue):
            run = self.runs.get(run_id)
            if run and run.status == RunStatus.PENDING:
                self.queue.pop(i)
                return run
                
        return None

    def update_run(self, run_id: str, status: RunStatus = None, task_states: Dict = None):
        run = self.runs.get(run_id)
        if not run:
            return
            
        if status:
            # State transition check
            # If server has CANCELLING, ignore RUNNING from worker
            if run.status == RunStatus.CANCELLING and status == RunStatus.RUNNING:
                pass
            else:
                run.status = status
                
            if status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                if not run.end_time:
                    run.end_time = time.time()
                    
        if task_states:
            run.tasks.update(task_states)

    def cancel_run(self, run_id: str):
        run = self.runs.get(run_id)
        if not run:
            return
            
        if run.status in [RunStatus.PENDING, RunStatus.RUNNING]:
            run.status = RunStatus.CANCELLING
