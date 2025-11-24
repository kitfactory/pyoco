from pyoco.core.models import Task
from pyoco.discovery.plugins import PluginRegistry


class DummyLoader:
    def __init__(self):
        self.tasks = {}

    def _register_task(self, name, task):
        self.tasks[name] = task


class VisionTask(Task):
    def __init__(self):
        super().__init__(func=self.run, name="vision_task")

    def run(self, ctx):
        return "vision"


def test_task_class_registration():
    loader = DummyLoader()
    registry = PluginRegistry(loader, "provider")

    registry.task_class(VisionTask)

    assert "vision_task" in loader.tasks
    record = registry.records[0]
    assert record["origin"] == "task_class"
    assert registry.warnings == []
