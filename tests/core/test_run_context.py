from pyoco.core.models import RunContext, TaskState


def test_run_context_serializes_task_records():
    ctx = RunContext(flow_name="test")
    ctx.tasks["alpha"] = TaskState.PENDING
    record = ctx.ensure_task_record("alpha")
    record.inputs = {"data": {"complex": object()}}
    record.output = object()
    data = ctx.serialize_task_records()
    assert "alpha" in data
    assert isinstance(data["alpha"]["inputs"]["data"], str)
    assert isinstance(data["alpha"]["output"], str)
