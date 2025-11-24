import pytest

from pyoco.server import api
from pyoco.server.models import (
    RunSubmitRequest,
    WorkerHeartbeatRequest,
    WorkerPollRequest,
)
from pyoco.core.models import RunStatus, TaskState
from pyoco.server.metrics import metrics
from pyoco.server.webhook import webhook_notifier


@pytest.fixture(autouse=True)
def clear_store(tmp_path):
    api.store.runs.clear()
    api.store.queue.clear()
    api.store.history.clear()
    api.store.max_runs = 50
    api.store.archive_dir = tmp_path
    api.store.log_limit_bytes = 1024 * 1024
    metrics.reset()
    webhook_notifier.reset()


@pytest.mark.asyncio
async def test_submit_run():
    resp = await api.submit_run(RunSubmitRequest(flow_name="test_flow", params={"x": 1}))
    assert resp.status == RunStatus.PENDING
    assert resp.run_id in api.store.runs
    assert resp.run_id in api.store.queue


@pytest.mark.asyncio
async def test_list_runs():
    await api.submit_run(RunSubmitRequest(flow_name="f1"))
    await api.submit_run(RunSubmitRequest(flow_name="f2"))
    runs = await api.list_runs()
    assert len(runs) >= 2


@pytest.mark.asyncio
async def test_get_run():
    resp = await api.submit_run(RunSubmitRequest(flow_name="f3"))
    data = await api.get_run(resp.run_id)
    assert data["run_id"] == resp.run_id
    assert data["status"] == RunStatus.PENDING.value


@pytest.mark.asyncio
async def test_cancel_run():
    resp = await api.submit_run(RunSubmitRequest(flow_name="f4"))
    await api.cancel_run(resp.run_id)
    data = await api.get_run(resp.run_id)
    assert data["status"] == RunStatus.CANCELLING.value


@pytest.mark.asyncio
async def test_worker_poll():
    await api.submit_run(RunSubmitRequest(flow_name="poll"))
    resp = await api.poll_work(WorkerPollRequest(worker_id="w1"))
    assert resp.run_id is not None
    assert resp.flow_name == "poll"
    resp2 = await api.poll_work(WorkerPollRequest(worker_id="w1"))
    assert resp2.run_id is None


@pytest.mark.asyncio
async def test_worker_heartbeat_and_cancel():
    resp = await api.submit_run(RunSubmitRequest(flow_name="hb"))
    run_id = resp.run_id
    heartbeat_resp = await api.heartbeat(
        run_id,
        WorkerHeartbeatRequest(
            task_states={"t1": TaskState.RUNNING.value},
            task_records={"t1": {"state": TaskState.RUNNING.value}},
            logs=[{"seq": 0, "task": "t1", "stream": "stdout", "text": "log"}],
            run_status=RunStatus.RUNNING,
        ),
    )
    assert heartbeat_resp.cancel_requested is False
    await api.cancel_run(run_id)
    heartbeat_resp2 = await api.heartbeat(
        run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.RUNNING,
        ),
    )
    assert heartbeat_resp2.cancel_requested is True


@pytest.mark.asyncio
async def test_logs_endpoint():
    resp = await api.submit_run(RunSubmitRequest(flow_name="logs"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[{"seq": 0, "task": "t1", "stream": "stdout", "text": "hello"}],
            run_status=RunStatus.RUNNING,
        ),
    )
    data = await api.get_logs(resp.run_id)
    assert data["logs"][0]["text"] == "hello"


@pytest.mark.asyncio
async def test_log_backpressure():
    api.store.log_limit_bytes = 8
    resp = await api.submit_run(RunSubmitRequest(flow_name="log_limit"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[{"seq": 1, "task": "t1", "stream": "stdout", "text": "abcdefghijk"}],
            run_status=RunStatus.RUNNING,
        ),
    )
    run = api.store.get_run(resp.run_id)
    assert "truncated" in run.logs[-1]["text"]


@pytest.mark.asyncio
async def test_run_retention_spills_to_disk(tmp_path):
    api.store.max_runs = 1
    api.store.archive_dir = tmp_path
    resp = await api.submit_run(RunSubmitRequest(flow_name="old"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.COMPLETED,
        ),
    )
    await api.submit_run(RunSubmitRequest(flow_name="new"))
    assert api.store.get_run(resp.run_id) is None
    assert (tmp_path / f"{resp.run_id}.json").exists()
