import pytest

from pyoco.core.models import RunStatus, TaskState
from pyoco.server import api
from pyoco.server.models import RunSubmitRequest, WorkerHeartbeatRequest
from pyoco.server.webhook import webhook_notifier


@pytest.fixture(autouse=True)
def setup_store(tmp_path):
    api.store.runs.clear()
    api.store.queue.clear()
    api.store.history.clear()
    api.store.max_runs = 50
    api.store.archive_dir = tmp_path
    yield
    webhook_notifier.reset()


@pytest.fixture
def capture_sender():
    events = []

    def sender(url, payload, headers, timeout):
        events.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})

    webhook_notifier.configure(url="memory://webhook", sender=sender, retries=1)
    return events


@pytest.mark.asyncio
async def test_webhook_fires_on_completion(capture_sender):
    resp = await api.submit_run(RunSubmitRequest(flow_name="foo"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={"t1": TaskState.RUNNING.value},
            task_records={},
            logs=[],
            run_status=RunStatus.RUNNING,
        ),
    )
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={"t1": TaskState.SUCCEEDED.value},
            task_records={"t1": {"state": TaskState.SUCCEEDED.value, "duration_ms": 1.0}},
            logs=[],
            run_status=RunStatus.COMPLETED,
        ),
    )
    assert len(capture_sender) == 1
    payload = capture_sender[0]["payload"]
    assert payload["event"] == "run.completed"
    assert payload["run_id"] == resp.run_id
    assert payload["tasks"]["t1"]["state"] == TaskState.SUCCEEDED.value


@pytest.mark.asyncio
async def test_webhook_retries_until_success():
    resp = await api.submit_run(RunSubmitRequest(flow_name="bar"))
    attempts = {"count": 0}
    events = []

    def flaky_sender(url, payload, headers, timeout):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("boom")
        events.append(payload)

    webhook_notifier.configure(url="memory://retry", sender=flaky_sender, retries=2)
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.FAILED,
        ),
    )
    assert attempts["count"] == 2
    assert len(events) == 1
    assert events[0]["event"] == "run.failed"
