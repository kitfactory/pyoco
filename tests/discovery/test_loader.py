import pytest
import os
import tempfile
import sys
from types import SimpleNamespace
from unittest.mock import patch
from pyoco.discovery.loader import TaskLoader
from pyoco.core.models import Task
from pyoco.schemas.config import PyocoConfig

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
