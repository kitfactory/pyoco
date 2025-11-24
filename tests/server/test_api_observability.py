import pytest

from pyoco.core.models import RunStatus, TaskState
from pyoco.server import api
from pyoco.server.metrics import metrics
from pyoco.server.models import RunSubmitRequest, WorkerHeartbeatRequest
from pyoco.server.webhook import webhook_notifier


@pytest.fixture(autouse=True)
def reset_state(tmp_path):
    api.store.runs.clear()
    api.store.queue.clear()
    api.store.history.clear()
    api.store.max_runs = 50
    api.store.archive_dir = tmp_path
    api.store.log_limit_bytes = 1024 * 1024
    metrics.reset()
    webhook_notifier.reset()


@pytest.mark.asyncio
async def test_list_runs_filters_and_limit():
    r1 = await api.submit_run(RunSubmitRequest(flow_name="alpha"))
    r2 = await api.submit_run(RunSubmitRequest(flow_name="beta"))
    await api.heartbeat(
        r1.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.RUNNING,
        ),
    )
    await api.heartbeat(
        r1.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.COMPLETED,
        ),
    )

    runs = await api.list_runs(status="PENDING", flow="beta", limit=1)
    assert len(runs) == 1
    assert runs[0]["run_id"] == r2.run_id


@pytest.mark.asyncio
async def test_run_detail_contains_summary():
    resp = await api.submit_run(RunSubmitRequest(flow_name="gamma"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={"t1": TaskState.RUNNING.value},
            task_records={
                "t1": {
                    "state": TaskState.SUCCEEDED.value,
                    "duration_ms": 5.5,
                    "ended_at": 1.2,
                }
            },
            logs=[],
            run_status=RunStatus.RUNNING,
        ),
    )
    run = await api.get_run(resp.run_id)
    assert run["task_summary"]["t1"]["duration_ms"] == 5.5


@pytest.mark.asyncio
async def test_logs_tail_filter():
    resp = await api.submit_run(RunSubmitRequest(flow_name="logger"))
    logs = []
    for seq in range(10):
        logs.append({"seq": seq, "task": "t", "stream": "stdout", "text": f"line{seq}"})
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=logs,
            run_status=RunStatus.RUNNING,
        ),
    )
    result = await api.get_logs(resp.run_id, tail=3)
    assert len(result["logs"]) == 3
    assert result["logs"][0]["text"] == "line7"


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_payload():
    resp = await api.submit_run(RunSubmitRequest(flow_name="metrics"))
    await api.heartbeat(
        resp.run_id,
        WorkerHeartbeatRequest(
            task_states={},
            task_records={},
            logs=[],
            run_status=RunStatus.RUNNING,
        ),
    )
    response = await api.prometheus_metrics()
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "pyoco_runs_total" in body
