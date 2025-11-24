import uuid
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..core.models import RunContext, RunStatus, TaskState
from .metrics import metrics
from .webhook import webhook_notifier

MAX_RUN_HISTORY = int(os.getenv("PYOCO_MAX_RUN_HISTORY", "50"))
RUN_ARCHIVE_DIR = Path(os.getenv("PYOCO_RUN_ARCHIVE_DIR", "artifacts/runs"))
MAX_LOG_BYTES_PER_TASK = int(os.getenv("PYOCO_MAX_LOG_BYTES", str(1024 * 1024)))

class StateStore:
    def __init__(self):
        self.runs: Dict[str, RunContext] = {}
        self.queue: List[str] = []
        self.history: List[str] = []
        self.max_runs = MAX_RUN_HISTORY
        self.archive_dir = RUN_ARCHIVE_DIR
        self.log_limit_bytes = MAX_LOG_BYTES_PER_TASK
        self.metrics = metrics
        self.webhook = webhook_notifier
        
    def create_run(self, flow_name: str, params: Dict) -> RunContext:
        run_id = str(uuid.uuid4())
        run_ctx = RunContext(
            run_id=run_id,
            flow_name=flow_name,
            params=params or {},
            status=RunStatus.PENDING,
            start_time=time.time()
        )
        
        self.runs[run_id] = run_ctx
        self.queue.append(run_id)
        self.history.append(run_id)
        self._enforce_retention()
        self.metrics.record_status_transition(None, run_ctx.status)
        return run_ctx

    def get_run(self, run_id: str) -> Optional[RunContext]:
        return self.runs.get(run_id)

    def list_runs(
        self,
        status: Optional[RunStatus] = None,
        flow: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[RunContext]:
        runs = list(self.runs.values())
        if status:
            runs = [r for r in runs if r.status == status]
        if flow:
            runs = [r for r in runs if r.flow_name == flow]
        runs.sort(key=lambda r: r.start_time or 0, reverse=True)
        if limit:
            runs = runs[:limit]
        return runs

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

    def update_run(self, run_id: str, status: RunStatus = None, task_states: Dict = None, task_records: Dict = None, logs: List[Dict[str, Any]] = None):
        run = self.runs.get(run_id)
        if not run:
            return
        previous_status = run.status

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
                    
        if run.status != previous_status:
            self.metrics.record_status_transition(previous_status, run.status)

        if task_states:
            for name, state in task_states.items():
                run.tasks[name] = TaskState(state) if isinstance(state, str) else state
        if task_records:
            for name, record in task_records.items():
                info = run.ensure_task_record(name)
                state_val = record.get("state")
                if state_val:
                    info.state = TaskState(state_val) if isinstance(state_val, str) else state_val
                info.started_at = record.get("started_at", info.started_at)
                info.ended_at = record.get("ended_at", info.ended_at)
                info.duration_ms = record.get("duration_ms", info.duration_ms)
                info.error = record.get("error", info.error)
                info.traceback = record.get("traceback", info.traceback)
                info.inputs = record.get("inputs", info.inputs)
                info.output = record.get("output", info.output)
                info.artifacts = record.get("artifacts", info.artifacts)
                self._record_task_metrics(run, name, info)
        if logs:
            for entry in logs:
                task_name = entry.get("task") or "unknown"
                text = entry.get("text", "")
                encoded_len = len(text.encode("utf-8"))
                current = run.log_bytes.get(task_name, 0)
                if current >= self.log_limit_bytes:
                    continue
                if current + encoded_len > self.log_limit_bytes:
                    allowed = max(self.log_limit_bytes - current, 0)
                    truncated_text = text[:allowed] + "\n[log truncated]"
                    entry = dict(entry)
                    entry["text"] = truncated_text
                    run.log_bytes[task_name] = self.log_limit_bytes
                else:
                    run.log_bytes[task_name] = current + encoded_len
                run.logs.append(entry)
        if status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            self._enforce_retention()
        if run.end_time and not run.metrics_run_observed:
            self.metrics.record_run_duration(run.flow_name, run.start_time, run.end_time)
            run.metrics_run_observed = True
        if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            if run.webhook_notified_status != run.status.value:
                if self.webhook.notify_run(run):
                    run.webhook_notified_status = run.status.value

    def cancel_run(self, run_id: str):
        run = self.runs.get(run_id)
        if not run:
            return
        previous = run.status
        if run.status in [RunStatus.PENDING, RunStatus.RUNNING]:
            run.status = RunStatus.CANCELLING
        if run.status != previous:
            self.metrics.record_status_transition(previous, run.status)

    def export_run(self, run: RunContext) -> Dict[str, Any]:
        return {
            "run_id": run.run_id,
            "flow_name": run.flow_name,
            "params": run.params,
            "status": run.status.value if hasattr(run.status, "value") else run.status,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "tasks": {name: state.value if hasattr(state, "value") else state for name, state in run.tasks.items()},
            "task_records": run.serialize_task_records(),
            "logs": run.logs,
            "metadata": run.metadata,
            "run_duration_ms": self._run_duration_ms(run),
            "task_summary": self._build_task_summary(run),
        }

    def _enforce_retention(self):
        removable_ids = [rid for rid in self.history if rid in self.runs]
        while len(self.runs) > self.max_runs and removable_ids:
            run_id = removable_ids.pop(0)
            run = self.runs.get(run_id)
            if not run:
                continue
            if run.status not in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                self.history.append(run_id)
                continue
            self._spill_run(run)
            self.runs.pop(run_id, None)
            if run_id in self.queue:
                self.queue.remove(run_id)
        self.history = [rid for rid in self.history if rid in self.runs]

    def _spill_run(self, run: RunContext):
        try:
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            path = self.archive_dir / f"{run.run_id}.json"
            with path.open("w", encoding="utf-8") as fp:
                json.dump(self.export_run(run), fp, indent=2)
        except Exception:
            pass

    def _record_task_metrics(self, run: RunContext, task_name: str, record):
        if task_name in run.metrics_recorded_tasks:
            return
        if record.duration_ms is None or record.ended_at is None:
            return
        self.metrics.record_task_duration(task_name, record.duration_ms)
        run.metrics_recorded_tasks.add(task_name)

    def _run_duration_ms(self, run: RunContext) -> Optional[float]:
        if run.start_time and run.end_time:
            return (run.end_time - run.start_time) * 1000.0
        return None

    def _build_task_summary(self, run: RunContext) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for name, record in run.task_records.items():
            summary[name] = {
                "state": record.state.value if hasattr(record.state, "value") else record.state,
                "duration_ms": record.duration_ms,
                "ended_at": record.ended_at,
            }
        return summary
