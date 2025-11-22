import pytest
from fastapi.testclient import TestClient
from pyoco.server.api import app, store
from pyoco.core.models import RunStatus, TaskState

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_store():
    store.runs.clear()
    store.queue.clear()

def test_submit_run():
    resp = client.post("/runs", json={"flow_name": "test_flow", "params": {"x": 1}})
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["status"] == RunStatus.PENDING.value
    
    # Verify it's in the store
    run_id = data["run_id"]
    assert run_id in store.runs
    assert run_id in store.queue

def test_list_runs():
    client.post("/runs", json={"flow_name": "f1"})
    client.post("/runs", json={"flow_name": "f2"})
    
    resp = client.get("/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2

def test_get_run():
    # Create a run
    resp = client.post("/runs", json={"flow_name": "f3"})
    run_id = resp.json()["run_id"]
    
    resp = client.get(f"/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["status"] == RunStatus.PENDING.value

def test_cancel_run():
    resp = client.post("/runs", json={"flow_name": "f4"})
    run_id = resp.json()["run_id"]
    
    resp = client.post(f"/runs/{run_id}/cancel")
    assert resp.status_code == 200
    
    # Check status
    resp = client.get(f"/runs/{run_id}")
    assert resp.json()["status"] == RunStatus.CANCELLING.value

def test_worker_poll():
    # Ensure queue has something
    client.post("/runs", json={"flow_name": "f5"})
    
    resp = client.post("/workers/poll", json={"worker_id": "w1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] is not None
    assert data["flow_name"] == "f5"
    
    # Poll again, should be empty (dequeued)
    resp = client.post("/workers/poll", json={"worker_id": "w1"})
    assert resp.json()["run_id"] is None

def test_worker_heartbeat():
    resp = client.post("/runs", json={"flow_name": "f6"})
    run_id = resp.json()["run_id"]
    
    # Update status
    resp = client.post(f"/runs/{run_id}/heartbeat", json={
        "task_states": {"t1": TaskState.RUNNING.value},
        "run_status": RunStatus.RUNNING.value
    })
    assert resp.status_code == 200
    assert resp.json()["cancel_requested"] is False
    
    # Check store update
    run = store.get_run(run_id)
    assert run.status == RunStatus.RUNNING
    assert run.tasks["t1"] == TaskState.RUNNING
    
    # Request cancel
    client.post(f"/runs/{run_id}/cancel")
    
    # Heartbeat should see cancel
    resp = client.post(f"/runs/{run_id}/heartbeat", json={
        "task_states": {},
        "run_status": RunStatus.RUNNING.value
    })
    assert resp.json()["cancel_requested"] is True
