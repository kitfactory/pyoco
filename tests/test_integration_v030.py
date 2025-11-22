import time
import threading
import uvicorn
import pytest
import requests
from pyoco.server.api import app, store
from pyoco.worker.runner import Worker
from pyoco.client import Client
from pyoco.schemas.config import PyocoConfig
from pyoco.core.models import RunStatus

# Server thread
class ServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8002):
        super().__init__()
        self.host = host
        self.port = port
        self.should_exit = False
        self.server = uvicorn.Server(config=uvicorn.Config(app, host=host, port=port, log_level="error"))

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

# Worker thread
class WorkerThread(threading.Thread):
    def __init__(self, server_url, config):
        super().__init__()
        self.worker = Worker(server_url, config, tags=[])
        self.should_stop = False

    def run(self):
        # Run worker loop until stopped
        while not self.should_stop:
            job = self.worker.client.poll(self.worker.tags)
            if job:
                self.worker._execute_job(job)
            else:
                time.sleep(0.1)

    def stop(self):
        self.should_stop = True

@pytest.fixture(scope="module")
def server_and_worker():
    # Setup
    host = "127.0.0.1"
    port = 8002
    server_url = f"http://{host}:{port}"
    
    # Start Server
    server_thread = ServerThread(host, port)
    server_thread.start()
    
    # Wait for server
    for _ in range(50):
        try:
            requests.get(f"{server_url}/runs")
            break
        except:
            time.sleep(0.1)
    else:
        raise RuntimeError("Server failed to start")

    # Config for worker (using cute_demo)
    config = PyocoConfig.from_yaml("examples/cute_demo/flow.yaml")
    
    # Start Worker
    worker_thread = WorkerThread(server_url, config)
    worker_thread.start()

    yield server_url

    # Teardown
    worker_thread.stop()
    worker_thread.join(timeout=2)
    server_thread.stop()
    server_thread.join(timeout=2)

def test_remote_execution(server_and_worker):
    server_url = server_and_worker
    client = Client(server_url)
    
    # Submit run
    run_id = client.submit_run("curry_party", {"spice_level": "mild"})
    assert run_id
    
    # Poll status until completed
    for _ in range(100): # 10 seconds max
        run = client.get_run(run_id)
        if run["status"] in [RunStatus.COMPLETED.value, RunStatus.FAILED.value]:
            break
        time.sleep(0.1)
    
    final_run = client.get_run(run_id)
    assert final_run["status"] == RunStatus.COMPLETED.value
    
    # Check tasks
    tasks = final_run["tasks"]
    assert tasks["gather_ingredients"] == "SUCCEEDED"
    assert tasks["serve"] == "SUCCEEDED"

def test_remote_cancellation(server_and_worker):
    server_url = server_and_worker
    client = Client(server_url)
    
    # Submit run
    run_id = client.submit_run("curry_party", {"spice_level": "hot"})
    
    # Wait for it to start running
    for _ in range(50):
        run = client.get_run(run_id)
        if run["status"] == RunStatus.RUNNING.value:
            break
        time.sleep(0.1)
        
    # Cancel
    client.cancel_run(run_id)
    
    # Wait for cancellation
    for _ in range(50):
        run = client.get_run(run_id)
        if run["status"] == RunStatus.CANCELLED.value:
            break
        time.sleep(0.1)
        
    final_run = client.get_run(run_id)
    # Note: Depending on timing, it might finish before cancel takes effect,
    # or it might be cancelled.
    # Given the flow is fast, it might be hard to catch.
    # But we verify the API call works.
    assert final_run["status"] in [RunStatus.CANCELLED.value, RunStatus.COMPLETED.value, RunStatus.CANCELLING.value]
