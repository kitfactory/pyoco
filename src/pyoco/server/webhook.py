from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, Optional

import httpx

from ..core.models import RunContext, RunStatus


class WebhookNotifier:
    def __init__(self) -> None:
        self.url: Optional[str] = None
        self.timeout: float = 3.0
        self.retries: int = 1
        self.secret: Optional[str] = None
        self.extra_headers: Dict[str, str] = {}
        self._sender: Optional[Callable[[str, Dict[str, Any], Dict[str, str], float], None]] = None
        self.last_error: Optional[str] = None
        self.load_from_env()

    def load_from_env(self) -> None:
        self.url = os.getenv("PYOCO_WEBHOOK_URL") or None
        self.timeout = float(os.getenv("PYOCO_WEBHOOK_TIMEOUT", "3.0"))
        self.retries = int(os.getenv("PYOCO_WEBHOOK_RETRIES", "1"))
        self.secret = os.getenv("PYOCO_WEBHOOK_SECRET") or None
        self.extra_headers = {}
        self.last_error = None
        self._sender = None

    def configure(
        self,
        *,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        sender: Optional[Callable[[str, Dict[str, Any], Dict[str, str], float], None]] = None,
    ) -> None:
        if url is not None:
            self.url = url
        if timeout is not None:
            self.timeout = timeout
        if retries is not None:
            self.retries = max(1, retries)
        if secret is not None:
            self.secret = secret
        if headers is not None:
            self.extra_headers = dict(headers)
        if sender is not None:
            self._sender = sender
        self.last_error = None

    def notify_run(self, run: RunContext) -> bool:
        if not self.url:
            return False
        payload = self._build_payload(run)
        sender = self._sender or self._http_sender
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.secret:
            headers.setdefault("X-Pyoco-Token", self.secret)

        last_exc: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                sender(self.url, payload, headers, self.timeout)
                self.last_error = None
                return True
            except Exception as exc:  # pragma: no cover - retries captured via tests
                last_exc = exc
                time.sleep(min(0.5, 0.1 * (attempt + 1)))
        if last_exc:
            self.last_error = str(last_exc)
        return False

    def _http_sender(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: float,
    ) -> None:
        httpx.post(url, json=payload, headers=headers, timeout=timeout)

    def _build_payload(self, run: RunContext) -> Dict[str, Any]:
        duration_ms = None
        if run.start_time and run.end_time:
            duration_ms = (run.end_time - run.start_time) * 1000.0
        return {
            "event": f"run.{run.status.value.lower()}",
            "run_id": run.run_id,
            "flow_name": run.flow_name,
            "status": run.status.value if isinstance(run.status, RunStatus) else run.status,
            "started_at": run.start_time,
            "ended_at": run.end_time,
            "duration_ms": duration_ms,
            "tasks": run.serialize_task_records(),
            "metadata": run.metadata,
        }

    def reset(self) -> None:
        self.load_from_env()


webhook_notifier = WebhookNotifier()
