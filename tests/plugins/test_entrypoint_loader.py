from types import SimpleNamespace
from unittest.mock import patch

from pyoco.discovery.loader import TaskLoader
from pyoco.schemas.config import PyocoConfig, DiscoveryConfig


def make_config():
    return PyocoConfig(version=1, flows={}, tasks={}, discovery=DiscoveryConfig())


def make_entry_point(name, hook):
    return SimpleNamespace(
        name=name,
        value=f"pkg:{hook.__name__}",
        module="pkg",
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
