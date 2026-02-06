import sys

import pytest

from pyoco import Flow, task
from pyoco.core.engine import Engine
from pyoco.core.models import RunContext


def test_run_restores_stdout_and_stderr():
    @task
    def hello(ctx):
        print("hello")
        print("error-line", file=sys.stderr)
        return "ok"

    flow = Flow(name="restore_streams")
    flow >> hello

    engine = Engine()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    engine.run(flow)

    assert sys.stdout is original_stdout
    assert sys.stderr is original_stderr


def test_exception_path_captures_stdout_and_stderr_logs():
    @task
    def boom(ctx):
        print("before-fail")
        print("stderr-fail", file=sys.stderr)
        raise RuntimeError("boom")

    flow = Flow(name="capture_on_error")
    flow >> boom

    run_ctx = RunContext()
    engine = Engine()
    with pytest.raises(RuntimeError):
        engine.run(flow, run_context=run_ctx)

    stdout_payload = "".join(entry["text"] for entry in run_ctx.logs if entry["task"] == "boom" and entry["stream"] == "stdout")
    stderr_payload = "".join(entry["text"] for entry in run_ctx.logs if entry["task"] == "boom" and entry["stream"] == "stderr")
    assert "before-fail" in stdout_payload
    assert "stderr-fail" in stderr_payload
