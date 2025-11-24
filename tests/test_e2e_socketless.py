import threading
import time

import pytest
from socketless_http import reset_ipc_state, switch_to_ipc_connection

from pyoco.client import Client
from pyoco.core.models import RunStatus
from pyoco.schemas.config import PyocoConfig
from pyoco.worker.runner import Worker

SOCKETLESS_URL = "http://testserver"


@pytest.fixture(scope="module", autouse=True)
def ipc_server():
    cleanup = switch_to_ipc_connection(
        "pyoco.server.api:app",
        reset_hook="pyoco.socketless_reset:reset_store",
        base_url=SOCKETLESS_URL,
        debug=True,
    )
    yield
    cleanup()


@pytest.fixture(autouse=True)
def reset_state():
    reset_ipc_state()


class WorkerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.config = PyocoConfig.from_yaml("examples/cute_demo/flow.yaml")
        self.worker = Worker(SOCKETLESS_URL, self.config, tags=[])
        self._stop_event = threading.Event()

    def run(self):
        print("[worker] start loop")
        while not self._stop_event.is_set():
            job = self.worker.client.poll(self.worker.tags)
            if job:
                print(f"[worker] got job {job.get('run_id')}")
                self.worker._execute_job(job)
            else:
                print("[worker] no job, sleep")
                self._stop_event.wait(2.0)
        print("[worker] stop loop")

    def stop(self):
        self._stop_event.set()


@pytest.fixture
def worker_thread():
    thread = WorkerThread()
    thread.start()
    yield
    thread.stop()
    thread.join(timeout=2)


def test_socketless_end_to_end(worker_thread):
    client = Client(SOCKETLESS_URL)
    run_id = client.submit_run("curry_party", {"spice_level": "mild"})
    assert run_id

    final_status = None
    for attempt in range(100):
        run = client.get_run(run_id)
        status = run["status"]
        print(f"[client] attempt {attempt} status={status}")
        if status in {RunStatus.COMPLETED.value, RunStatus.FAILED.value}:
            final_status = status
            break
        time.sleep(2.0)

    assert final_status == RunStatus.COMPLETED.value
