import pytest
import os
import tempfile
import sys
from types import SimpleNamespace
from unittest.mock import patch
from pyoco.discovery.loader import TaskLoader
from pyoco.core.models import Task
from pyoco.schemas.config import FlowConfig, PyocoConfig
from pyoco.dsl.graph import build_flow_from_graph

def test_loader_strict_collision():
    # Mock config with collision
    # We need to mock loading modules that have tasks
    # Hard to mock importlib without complex patching.
    # Let's test _register_task directly.
    
    loader = TaskLoader(config=None, strict=True)
    t1 = Task(func=lambda: None, name="A")
    t2 = Task(func=lambda: None, name="A")
    
    loader._register_task("A", t1)
    
    with pytest.raises(ValueError, match="Strict mode enabled"):
        loader._register_task("A", t2)

def test_loader_explicit_priority():
    loader = TaskLoader(config=None, strict=True)
    t_explicit = Task(func=lambda: 1, name="A")
    t_implicit = Task(func=lambda: 2, name="A")
    
    # Pre-populate explicit
    loader._explicit_tasks.add("A")
    loader.tasks["A"] = t_explicit
    
    # Try to register implicit
    loader._register_task("A", t_implicit)
    
    # Should still be explicit
    assert loader.tasks["A"] == t_explicit

def test_loader_env_modules(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        module_path = os.path.join(tmpdir, "tasks.py")
        with open(module_path, "w") as f:
            f.write(
                "from pyoco.dsl.syntax import task\n"
                "\n"
                "@task\n"
                "def MyJob(ctx):\n"
                "    return \"ok\"\n"
            )

        sys.path.insert(0, tmpdir)
        monkeypatch.setenv("PYOCO_DISCOVERY_MODULES", "tasks")
        try:
            config = PyocoConfig(version=1, flow=None, tasks={})
            with patch("pyoco.discovery.loader.iter_entry_points", return_value=[]):
                loader = TaskLoader(config=config)
                loader.load()
            assert "MyJob" in loader.tasks
        finally:
            sys.path.pop(0)
            sys.modules.pop("tasks", None)


def test_loader_resolves_task_use_aliases():
    config = PyocoConfig(
        version=1,
        flow=None,
        tasks={
            "classify": SimpleNamespace(use="vision/image_classify", callable=None, inputs={}, outputs=[]),
            "classify2": SimpleNamespace(use="vision/image_classify", callable=None, inputs={}, outputs=[]),
        },
    )
    loader = TaskLoader(config=config)
    source = Task(func=lambda: "ok", name="vision/image_classify")
    loader.tasks[source.name] = source

    loader._resolve_task_uses()

    assert "classify" in loader.tasks
    assert "classify2" in loader.tasks
    assert loader.tasks["classify"] is not source
    assert loader.tasks["classify2"] is not source
    assert loader.tasks["classify"].func is source.func
    assert loader.tasks["classify2"].func is source.func


def test_loader_task_use_applies_local_overrides():
    config = PyocoConfig(
        version=1,
        flow=None,
        tasks={
            "classify": SimpleNamespace(
                use="vision/image_classify",
                callable=None,
                inputs={"image": "$ctx.params.path"},
                outputs=["scratch.classify"],
            ),
        },
    )
    loader = TaskLoader(config=config)
    source = Task(func=lambda: "ok", name="vision/image_classify")
    source.inputs = {"seed": "$ctx.params.seed"}
    loader.tasks[source.name] = source

    loader._resolve_task_uses()

    alias = loader.tasks["classify"]
    assert alias.inputs["seed"] == "$ctx.params.seed"
    assert alias.inputs["image"] == "$ctx.params.path"
    assert alias.outputs == ["scratch.classify"]


def test_loader_task_use_requires_registered_target():
    config = PyocoConfig(
        version=1,
        flow=None,
        tasks={
            "classify": SimpleNamespace(use="vision/image_classify", callable=None, inputs={}, outputs=[]),
        },
    )
    loader = TaskLoader(config=config)

    with pytest.raises(ValueError, match="unknown task 'vision/image_classify'"):
        loader._resolve_task_uses()


def test_loader_task_use_supports_graph_with_multiple_local_names():
    config = PyocoConfig(
        version=1,
        flow=FlowConfig(graph="classify >> classify2", defaults={}),
        tasks={
            "classify": SimpleNamespace(use="vision/image_classify", callable=None, inputs={}, outputs=[]),
            "classify2": SimpleNamespace(use="vision/image_classify", callable=None, inputs={}, outputs=[]),
        },
    )
    loader = TaskLoader(config=config)
    loader.tasks["vision/image_classify"] = Task(func=lambda: "ok", name="vision/image_classify")

    loader._resolve_task_uses()
    flow = build_flow_from_graph(graph=config.flow.graph, tasks=loader.tasks, flow_name="main")
    task_map = {task.name: task for task in flow.tasks}

    assert set(task_map) == {"classify", "classify2"}
    assert task_map["classify2"] in task_map["classify"].dependents
