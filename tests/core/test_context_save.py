import os
import shutil
import tempfile
from pyoco.core.context import Context
from pyoco.core.engine import Engine
from pyoco.core.models import Task, Flow

def test_context_save_artifact():
    # Create a temporary directory for artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = Context(artifact_dir=tmpdir)
        
        # Test saving string
        path1 = ctx.save_artifact("test.txt", "hello world")
        assert os.path.exists(path1)
        with open(path1, "r") as f:
            assert f.read() == "hello world"
        assert ctx.artifacts["test.txt"]["path"] == path1
        
        # Test saving bytes
        path2 = ctx.save_artifact("test.bin", b"\x00\x01")
        assert os.path.exists(path2)
        with open(path2, "rb") as f:
            assert f.read() == b"\x00\x01"
            
        # Test nested path
        path3 = ctx.save_artifact("subdir/nested.txt", "nested")
        assert os.path.exists(path3)
        assert os.path.dirname(path3).endswith("subdir")

def test_engine_save_config():
    # Define a task that returns a dict
    def my_task():
        return {"a": 1, "b": 2}
        
    t = Task(
        func=my_task,
        name="A",
        outputs=[
            "scratch.my_data"
        ]
    )
    
    flow = Flow()
    flow.add_task(t)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize engine
        engine = Engine()
        
        # Run flow
        # Monkeypatch Context for this test to use tmpdir
        original_init = Context.__init__
        def mocked_init(self, *args, **kwargs):
            kwargs["artifact_dir"] = tmpdir
            original_init(self, *args, **kwargs)
            
        Context.__init__ = mocked_init
        
        try:
            ctx = engine.run(flow)
            
            # Verify context update
            assert "my_data" in ctx.scratch
            assert ctx.scratch["my_data"] == {"a": 1, "b": 2}
            
        finally:
            # Restore Context
            Context.__init__ = original_init

def test_engine_save_nested_ctx():
    def my_task():
        return 42
        
    t = Task(
        func=my_task,
        name="B",
        outputs=[
            "scratch.deep.nested.value"
        ]
    )
    
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    ctx = engine.run(flow)
    
    assert ctx.scratch["deep"]["nested"]["value"] == 42
