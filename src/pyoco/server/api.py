from fastapi import FastAPI, HTTPException
from typing import List, Optional
from .store import StateStore
from .models import (
    RunSubmitRequest, RunResponse, 
    WorkerPollRequest, WorkerPollResponse,
    WorkerHeartbeatRequest, WorkerHeartbeatResponse
)
from ..core.models import RunContext, RunStatus

app = FastAPI(title="Pyoco Kanban Server")
store = StateStore()

@app.post("/runs", response_model=RunResponse)
def submit_run(req: RunSubmitRequest):
    run_ctx = store.create_run(req.flow_name, req.params)
    return RunResponse(run_id=run_ctx.run_id, status=run_ctx.status)

@app.get("/runs", response_model=List[RunContext])
def list_runs(status: Optional[RunStatus] = None):
    runs = store.list_runs()
    if status:
        runs = [r for r in runs if r.status == status]
    return runs

@app.get("/runs/{run_id}", response_model=RunContext)
def get_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    store.cancel_run(run_id)
    return {"status": "CANCELLING"}

@app.post("/workers/poll", response_model=WorkerPollResponse)
def poll_work(req: WorkerPollRequest):
    # In v0.3.0, we ignore worker_id and tags for simplicity
    run = store.dequeue()
    if run:
        # Mark as RUNNING? Or wait for worker to say so?
        # Ideally, worker should confirm start.
        # But for now, let's assume dequeue means "assigned".
        # We update status to RUNNING when worker sends first heartbeat?
        # Or here? Let's do it here to prevent re-queueing if logic was complex.
        # But store.dequeue removes from queue.
        # Status is still PENDING until worker starts.
        return WorkerPollResponse(
            run_id=run.run_id,
            flow_name=run.flow_name,
            params=run.params
        )
    return WorkerPollResponse()

@app.post("/runs/{run_id}/heartbeat", response_model=WorkerHeartbeatResponse)
def heartbeat(run_id: str, req: WorkerHeartbeatRequest):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    store.update_run(run_id, status=req.run_status, task_states=req.task_states)
    
    # Check if cancellation was requested
    cancel_requested = (run.status == RunStatus.CANCELLING)
    
    return WorkerHeartbeatResponse(cancel_requested=cancel_requested)
