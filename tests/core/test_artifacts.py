import os
import pytest
from pyoco.core.context import Context
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine

def test_context_save_artifact_string(tmp_path):
    ctx = Context(artifact_dir=str(tmp_path))
    path = ctx.save_artifact("test.txt", "hello world")
    
    assert os.path.exists(path)
    assert path == str(tmp_path / "test.txt")
    with open(path, "r") as f:
        assert f.read() == "hello world"
        
    assert "test.txt" in ctx.artifacts
    assert ctx.artifacts["test.txt"]["type"] == "str"

def test_context_save_artifact_bytes(tmp_path):
    ctx = Context(artifact_dir=str(tmp_path))
    data = b"\x00\x01\x02"
    path = ctx.save_artifact("test.bin", data)
    
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == data
        
    assert ctx.artifacts["test.bin"]["type"] == "bytes"

def test_context_save_artifact_object(tmp_path):
    ctx = Context(artifact_dir=str(tmp_path))
    data = {"a": 1, "b": 2}
    path = ctx.save_artifact("test.json", data)
    
    assert os.path.exists(path)
    with open(path, "r") as f:
        content = f.read()
        assert "{'a': 1, 'b': 2}" in content # str(dict) representation
        
    assert ctx.artifacts["test.json"]["type"] == "object"
