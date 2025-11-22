import pytest
import os
import tempfile
from pyoco.discovery.loader import TaskLoader
from pyoco.core.models import Task
from pyoco.schemas.config import PyocoConfig, DiscoveryConfig, TaskConfig

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

def test_loader_glob():
    # Create temp python file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy module structure
        # tmpdir/jobs/myjob.py
        jobs_dir = os.path.join(tmpdir, "jobs")
        os.makedirs(jobs_dir)
        with open(os.path.join(jobs_dir, "myjob.py"), "w") as f:
            f.write("from pyoco.dsl.syntax import task\n@task\ndef MyJob(ctx): pass\n")
            
        # We need to add tmpdir to sys.path so importlib works
        import sys
        sys.path.insert(0, tmpdir)
        
        try:
            config = PyocoConfig(
                version=1, flows={}, tasks={},
                discovery=DiscoveryConfig(glob_modules=[f"{jobs_dir}/*.py"]),
                runtime=None
            )
            
            loader = TaskLoader(config=config)
            
            # We need to patch _load_glob_modules logic because it assumes relative path from CWD
            # The implementation uses os.path.relpath(file_path).
            # If we run from CWD, and tmpdir is elsewhere, relpath might be complex.
            # And importlib needs module path.
            # If tmpdir is in sys.path, then "jobs.myjob" is importable.
            # But relpath might be "/tmp/xyz/jobs/myjob.py".
            # If we are in /home/kitfactory/workspace/pyoco, relpath is ../../../tmp...
            # That won't convert to module name easily.
            
            # Let's adjust the test to change CWD to tmpdir
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Now glob pattern should be "jobs/*.py"
                config.discovery.glob_modules = ["jobs/*.py"]
                loader = TaskLoader(config=config)
                loader.load()
                
                assert "MyJob" in loader.tasks
            finally:
                os.chdir(cwd)
                
        finally:
            sys.path.pop(0)
