import threading
import time

from pyoco import Flow, task
from pyoco.core.engine import Engine
from pyoco.core.models import RunContext, RunStatus, TaskState


def test_cancel_stops_before_next_task_in_dag_flow():
    started = threading.Event()
    events = []

    @task
    def first(ctx):
        started.set()
        time.sleep(0.2)
        events.append("first")
        return "first"

    @task
    def second(ctx):
        events.append("second")
        return "second"

    flow = Flow("cancel_boundary_dag")
    flow >> first >> second

    engine = Engine()
    run_ctx = RunContext()

    thread = threading.Thread(target=lambda: engine.run(flow, run_context=run_ctx))
    thread.start()

    assert started.wait(timeout=1.0)
    engine.cancel(run_ctx.run_id)

    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert events == ["first"]
    assert run_ctx.status == RunStatus.CANCELLED
    assert run_ctx.tasks["first"] == TaskState.SUCCEEDED
    assert run_ctx.tasks["second"] == TaskState.CANCELLED


def test_cancel_stops_repeat_before_next_iteration():
    started = threading.Event()
    calls = []

    @task
    def step(ctx):
        calls.append(time.time())
        if len(calls) == 1:
            started.set()
            time.sleep(0.2)
        return len(calls)

    flow = Flow("cancel_boundary_repeat")
    flow >> (step)[3]

    engine = Engine()
    run_ctx = RunContext()

    thread = threading.Thread(target=lambda: engine.run(flow, run_context=run_ctx))
    thread.start()

    assert started.wait(timeout=1.0)
    engine.cancel(run_ctx.run_id)

    thread.join(timeout=2.0)
    assert not thread.is_alive()
    assert len(calls) == 1
    assert run_ctx.status == RunStatus.CANCELLED
    assert run_ctx.tasks["step"] == TaskState.SUCCEEDED
