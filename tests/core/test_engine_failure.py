import pytest
import time
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine

def test_fail_stop():
    def fail_task():
        raise ValueError("Boom")
        
    t = Task(func=fail_task, name="A", fail_policy="stop")
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    with pytest.raises(ValueError, match="Boom"):
        engine.run(flow)

def test_fail_isolate():
    # A (fails) -> B (dep on A)
    # C (independent)
    
    def fail_task():
        raise ValueError("Boom")
        
    def success_task():
        return "ok"
        
    t_a = Task(func=fail_task, name="A", fail_policy="isolate")
    t_b = Task(func=success_task, name="B") # B depends on A
    t_c = Task(func=success_task, name="C")
    
    flow = Flow()
    flow.add_task(t_a)
    flow.add_task(t_b)
    flow.add_task(t_c)
    
    # Manually set dependencies since DSL isn't used here
    t_b.dependencies.add(t_a)
    t_a.dependents.add(t_b)
    
    engine = Engine()
    ctx = engine.run(flow)
    
    # A should fail but not raise
    # B should NOT run (skipped/failed)
    # C should run
    
    assert "C" in ctx.results
    assert ctx.results["C"] == "ok"
    assert "A" not in ctx.results
    assert "B" not in ctx.results

def test_retry():
    attempts = 0
    def flaky_task():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Transient error")
        return "success"
        
    t = Task(func=flaky_task, name="A", retries=3)
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    ctx = engine.run(flow)
    
    assert ctx.results["A"] == "success"
    assert attempts == 3

def test_retry_exhausted():
    attempts = 0
    def always_fail():
        nonlocal attempts
        attempts += 1
        raise ValueError("Permanent error")
        
    t = Task(func=always_fail, name="A", retries=2)
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    with pytest.raises(ValueError, match="Permanent error"):
        engine.run(flow)
    
    assert attempts == 3 # Initial + 2 retries

def test_timeout():
    def slow_task():
        time.sleep(0.5)
        return "done"
        
    t = Task(func=slow_task, name="A", timeout_sec=0.1)
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    with pytest.raises(TimeoutError, match="exceeded timeout"):
        engine.run(flow)
