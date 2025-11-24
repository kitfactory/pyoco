from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import List, Optional, Dict, Any
from .store import StateStore
from .models import (
    RunSubmitRequest, RunResponse,
    WorkerPollRequest, WorkerPollResponse,
    WorkerHeartbeatRequest, WorkerHeartbeatResponse
)
from ..core.models import RunStatus
from .metrics import metrics, metrics_content_type

app = FastAPI(title="Pyoco Kanban Server")
store = StateStore()

@app.post("/runs", response_model=RunResponse)
async def submit_run(req: RunSubmitRequest):
    run_ctx = store.create_run(req.flow_name, req.params)
    return RunResponse(run_id=run_ctx.run_id, status=run_ctx.status)

@app.get("/runs")
async def list_runs(
    status: Optional[str] = None,
    flow: Optional[str] = None,
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    status_enum = _parse_status(status)
    limit_value = limit if isinstance(limit, int) else None
    runs = store.list_runs(status=status_enum, flow=flow, limit=limit_value)
    return [store.export_run(r) for r in runs]

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return store.export_run(run)

@app.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    store.cancel_run(run_id)
    return {"status": "CANCELLING"}

@app.post("/workers/poll", response_model=WorkerPollResponse)
async def poll_work(req: WorkerPollRequest):
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
async def heartbeat(run_id: str, req: WorkerHeartbeatRequest):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    store.update_run(
        run_id,
        status=req.run_status,
        task_states=req.task_states,
        task_records=req.task_records,
        logs=req.logs
    )
    
    # Check if cancellation was requested
    cancel_requested = (run.status == RunStatus.CANCELLING)
    
    return WorkerHeartbeatResponse(cancel_requested=cancel_requested)

@app.get("/runs/{run_id}/logs")
async def get_logs(run_id: str, task: Optional[str] = None, tail: Optional[int] = None):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    logs = run.logs
    if task:
        logs = [entry for entry in logs if entry["task"] == task]
    if tail:
        logs = logs[-tail:]
    return {"run_status": run.status, "logs": logs}


@app.get("/metrics")
async def prometheus_metrics():
    payload = metrics.render_latest()
    return PlainTextResponse(payload, media_type=metrics_content_type())


def _parse_status(value: Optional[str]) -> Optional[RunStatus]:
    if not value:
        return None
    if isinstance(value, RunStatus):
        return value
    try:
        return RunStatus(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status '{value}'")
