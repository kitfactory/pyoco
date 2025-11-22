import httpx
from typing import Dict, List, Optional, Any
from ..core.models import RunStatus, TaskState

class WorkerClient:
    def __init__(self, server_url: str, worker_id: str):
        self.server_url = server_url.rstrip("/")
        self.worker_id = worker_id
        self.client = httpx.Client(base_url=self.server_url)

    def poll(self, tags: List[str] = []) -> Optional[Dict[str, Any]]:
        try:
            resp = self.client.post("/workers/poll", json={
                "worker_id": self.worker_id,
                "tags": tags
            })
            resp.raise_for_status()
            data = resp.json()
            if data.get("run_id"):
                return data
            return None
        except Exception as e:
            print(f"Poll failed: {e}")
            return None

    def heartbeat(self, run_id: str, task_states: Dict[str, TaskState], run_status: RunStatus) -> bool:
        """
        Sends heartbeat. Returns True if cancellation is requested.
        """
        try:
            # Convert Enums to values
            states_json = {k: v.value for k, v in task_states.items()}
            status_value = run_status.value
            
            resp = self.client.post(f"/runs/{run_id}/heartbeat", json={
                "task_states": states_json,
                "run_status": status_value
            })
            resp.raise_for_status()
            return resp.json().get("cancel_requested", False)
        except Exception as e:
            print(f"Heartbeat failed: {e}")
            return False
