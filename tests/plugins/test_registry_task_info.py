import pytest

from pyoco.discovery.plugins import PluginRegistry
from pyoco.core.exceptions import MissingTaskMetadataError


class DummyLoader:
    def __init__(self):
        self.task_infos = {}

    def _register_task_info(self, info):
        self.task_infos[info.name] = info

    def _register_task(self, name, task):
        pass


def test_task_info_registration_defaults_origin():
    loader = DummyLoader()
    registry = PluginRegistry(loader, "demo")
    registry.task_info(
        name="task_a",
        summary="summary",
        inputs=[{"name": "x", "type": "str", "required": True}],
        outputs=[{"name": "y", "type": "str", "required": False}],
        usage="Use task_a in your flow with input x.",
    )
    assert "task_a" in registry.task_infos
    assert registry.task_infos["task_a"].origin == "demo"
    assert registry.task_infos["task_a"].usage == "Use task_a in your flow with input x."
    assert "task_a" in loader.task_infos


def test_task_info_requires_fields():
    loader = DummyLoader()
    registry = PluginRegistry(loader, "demo")
    with pytest.raises(MissingTaskMetadataError):
        registry.task_info(name="task_a", summary=None, inputs=[], outputs=[])
