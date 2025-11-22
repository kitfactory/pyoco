from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from ..core.models import RunStatus, TaskState

class RunSubmitRequest(BaseModel):
    flow_name: str
    params: Dict[str, Any] = {}
    tags: List[str] = []

class RunResponse(BaseModel):
    run_id: str
    status: RunStatus

class WorkerPollRequest(BaseModel):
    worker_id: str
    tags: List[str] = []

class WorkerPollResponse(BaseModel):
    run_id: Optional[str] = None
    flow_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class WorkerHeartbeatRequest(BaseModel):
    task_states: Dict[str, TaskState]
    run_status: RunStatus

class WorkerHeartbeatResponse(BaseModel):
    cancel_requested: bool
