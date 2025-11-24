from pyoco.core.models import Task
from pyoco.discovery.plugins import PluginRegistry


class DummyLoader:
    def __init__(self):
        self.tasks = {}

    def _register_task(self, name, task):
        self.tasks[name] = task


def test_callable_registration_warns():
    loader = DummyLoader()
    registry = PluginRegistry(loader, "demo")

    @registry.task(name="callable_task")
    def foo(ctx):
        return "ok"

    assert any("callable" in w for w in registry.warnings)


def test_plain_task_warns():
    loader = DummyLoader()
    registry = PluginRegistry(loader, "demo")
    registry.add(Task(func=lambda ctx: None, name="legacy"))

    assert any("plain Task" in w for w in registry.warnings)
