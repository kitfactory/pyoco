import httpx
from typing import Dict, List, Optional, Any
from .core.models import RunStatus, TaskState, RunContext

class Client:
    def __init__(self, server_url: str, client_id: str = "cli"):
        self.server_url = server_url.rstrip("/")
        self.client_id = client_id
        self.client = httpx.Client(base_url=self.server_url)

    def submit_run(self, flow_name: str, params: Dict[str, Any], tags: List[str] = []) -> str:
        resp = self.client.post("/runs", json={
            "flow_name": flow_name,
            "params": params,
            "tags": tags
        })
        resp.raise_for_status()
        return resp.json()["run_id"]

    def list_runs(
        self,
        status: Optional[str] = None,
        flow: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        params = {}
        if status:
            params["status"] = status
        if flow:
            params["flow"] = flow
        if limit:
            params["limit"] = limit
        resp = self.client.get("/runs", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_run(self, run_id: str) -> Dict:
        resp = self.client.get(f"/runs/{run_id}")
        resp.raise_for_status()
        return resp.json()

    def cancel_run(self, run_id: str):
        resp = self.client.post(f"/runs/{run_id}/cancel")
        resp.raise_for_status()

    def poll(self, tags: List[str] = []) -> Optional[Dict[str, Any]]:
        try:
            resp = self.client.post("/workers/poll", json={
                "worker_id": self.client_id,
                "tags": tags
            })
            resp.raise_for_status()
            data = resp.json()
            if data.get("run_id"):
                return data
            return None
        except Exception as e:
            # print(f"Poll failed: {e}")
            return None

    def heartbeat(self, run_ctx: RunContext) -> bool:
        """
        Sends heartbeat. Returns True if cancellation is requested.
        """
        try:
            states_json = {k: v.value if hasattr(v, 'value') else v for k, v in run_ctx.tasks.items()}
            status_value = run_ctx.status.value if hasattr(run_ctx.status, 'value') else run_ctx.status
            payload = {
                "task_states": states_json,
                "task_records": run_ctx.serialize_task_records(),
                "logs": run_ctx.drain_logs(),
                "run_status": status_value
            }
            resp = self.client.post(f"/runs/{run_ctx.run_id}/heartbeat", json=payload)
            resp.raise_for_status()
            return resp.json().get("cancel_requested", False)
        except Exception as e:
            print(f"Heartbeat failed: {e}")
            return False

    def get_run_logs(self, run_id: str, task: Optional[str] = None, tail: Optional[int] = None) -> Dict[str, Any]:
        params = {}
        if task:
            params["task"] = task
        if tail:
            params["tail"] = tail
        resp = self.client.get(f"/runs/{run_id}/logs", params=params)
        resp.raise_for_status()
        return resp.json()
