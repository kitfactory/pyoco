import pytest
from pyoco.core.context import Context

def test_resolve_literal():
    ctx = Context()
    assert ctx.resolve(1) == 1
    assert ctx.resolve("hello") == "hello"
    assert ctx.resolve(None) is None

def test_resolve_node_output():
    ctx = Context()
    ctx.results["A"] = 100
    ctx.results["B"] = {"x": 1, "y": 2}
    
    assert ctx.resolve("$node.A.output") == 100
    assert ctx.resolve("$node.B.output") == {"x": 1, "y": 2}

def test_resolve_node_output_nested():
    ctx = Context()
    ctx.results["B"] = {"x": 1, "y": 2}
    
    assert ctx.resolve("$node.B.output.x") == 1
    assert ctx.resolve("$node.B.output.y") == 2

def test_resolve_ctx_params():
    ctx = Context(params={"foo": "bar", "num": 42})
    
    assert ctx.resolve("$ctx.params.foo") == "bar"
    assert ctx.resolve("$ctx.params.num") == 42

def test_resolve_env(monkeypatch):
    monkeypatch.setenv("TEST_ENV_VAR", "found_me")
    ctx = Context()
    
    assert ctx.resolve("$env.TEST_ENV_VAR") == "found_me"

def test_resolve_missing_node():
    ctx = Context()
    with pytest.raises(KeyError):
        ctx.resolve("$node.Missing.output")

def test_resolve_missing_param():
    ctx = Context()
    with pytest.raises(KeyError):
        ctx.resolve("$ctx.params.missing")

def test_resolve_invalid_format():
    ctx = Context()
    # Should be treated as literal if it doesn't match known patterns?
    # Or raise error? Spec says "Selectors: $ctx.*, $flow.*, $env.*, $node.<Name>.output"
    # Let's assume anything starting with $ that isn't a known selector is just a string for now,
    # unless we want strict validation.
    # For now, let's expect it to return as-is if it doesn't match the specific patterns we implement.
    assert ctx.resolve("$unknown.pattern") == "$unknown.pattern"
