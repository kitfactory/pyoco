from types import SimpleNamespace
from unittest.mock import patch

from pyoco.discovery.loader import TaskLoader
from pyoco.schemas.config import PyocoConfig


def make_config():
    return PyocoConfig(version=1, flow=None, tasks={})


def make_entry_point(name, hook):
    return SimpleNamespace(
        name=name,
        value=f"pkg:{hook.__name__}",
        module="pkg",
        dist=SimpleNamespace(version="1.2.3"),
        load=lambda: hook,
    )


def test_entrypoint_registers_tasks():
    config = make_config()

    def plugin(registry):
        @registry.task(name="ext_task")
        def ext(ctx):
            return "ok"

    with patch(
        "pyoco.discovery.loader.iter_entry_points",
        return_value=[make_entry_point("demo", plugin)],
    ):
        loader = TaskLoader(config)
        loader.load()

    assert "ext_task" in loader.tasks
    tasks = loader.plugin_reports[0]["tasks"]
    assert tasks[0]["name"] == "ext_task"
    assert tasks[0]["origin"] == "callable"
    assert loader.plugin_reports[0]["version"] == "1.2.3"


def test_entrypoint_error_is_reported():
    config = make_config()

    def bad_plugin(registry):
        raise RuntimeError("boom")

    with patch(
        "pyoco.discovery.loader.iter_entry_points",
        return_value=[make_entry_point("bad", bad_plugin)],
    ):
        loader = TaskLoader(config)
        loader.load()

    assert loader.plugin_reports[0]["error"].startswith("boom")


def test_entrypoint_serializes_task_info():
    config = make_config()

    def plugin(registry):
        @registry.task(name="ext_task")
        def ext(ctx):
            return "ok"

        registry.task_info(
            name="ext_task",
            summary="External demo task",
            inputs=[{"name": "x", "type": "str", "required": True}],
            outputs=[{"name": "y", "type": "str", "required": False}],
            usage="Use ext_task by setting tasks.ext_task.callable in flow.yaml.",
        )

    with patch(
        "pyoco.discovery.loader.iter_entry_points",
        return_value=[make_entry_point("demo", plugin)],
    ):
        loader = TaskLoader(config)
        loader.load()

    task_infos = loader.plugin_reports[0]["task_infos"]
    assert task_infos[0]["name"] == "ext_task"
    assert task_infos[0]["usage"].startswith("Use ext_task")
