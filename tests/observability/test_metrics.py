import pytest

from pyoco.core.models import RunStatus, TaskState
from pyoco.server.store import StateStore
from pyoco.server.metrics import metrics


@pytest.fixture(autouse=True)
def store_with_metrics(tmp_path):
    metrics.reset()
    store = StateStore()
    store.archive_dir = tmp_path
    store.metrics = metrics
    yield store


def test_run_lifecycle_metrics(store_with_metrics):
    store: StateStore = store_with_metrics
    run = store.create_run("demo", {"x": 1})
    store.update_run(run.run_id, status=RunStatus.RUNNING)
    store.update_run(
        run.run_id,
        status=RunStatus.COMPLETED,
        task_records={
            "task_alpha": {
                "state": TaskState.SUCCEEDED.value,
                "duration_ms": 12.0,
                "ended_at": run.start_time + 0.2,
            }
        },
    )

    payload = metrics.render_latest().decode("utf-8")
    assert 'pyoco_runs_total{status="PENDING"}' in payload
    assert 'pyoco_runs_total{status="RUNNING"}' in payload
    assert 'pyoco_runs_total{status="COMPLETED"}' in payload
    assert "pyoco_runs_in_progress 0.0" in payload
    assert 'pyoco_task_duration_seconds_sum{task="task_alpha"}' in payload
    assert 'pyoco_run_duration_seconds_sum{flow="demo"}' in payload
