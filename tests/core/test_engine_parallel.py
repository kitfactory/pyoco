import time
import pytest
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine
from pyoco.core.context import Context

def slow_task(ctx, name, delay=0.1):
    time.sleep(delay)
    return f"{name}_done"

def test_parallel_execution_speed():
    # A and B are independent. Should run in parallel.
    # Total time should be around 0.1s, not 0.2s.
    
    t_a = Task(func=lambda ctx: slow_task(ctx, "A"), name="A")
    t_b = Task(func=lambda ctx: slow_task(ctx, "B"), name="B")
    
    flow = Flow(name="parallel_flow")
    flow.add_task(t_a)
    flow.add_task(t_b)
    
    engine = Engine()
    start = time.time()
    ctx = engine.run(flow)
    duration = time.time() - start
    
    assert ctx.results["A"] == "A_done"
    assert ctx.results["B"] == "B_done"
    
    # Allow some overhead, but it should be significantly less than sum
    assert duration < 0.18  # 0.1s + overhead. If sequential, it would be > 0.2s

def test_diamond_dependency():
    # A -> (B & C) -> D
    # B and C should run in parallel
    
    results = []
    
    def task_record(ctx, name, delay=0):
        if delay:
            time.sleep(delay)
        results.append(name)
        return name
        
    t_a = Task(func=lambda ctx: task_record(ctx, "A"), name="A")
    t_b = Task(func=lambda ctx: task_record(ctx, "B", 0.05), name="B")
    t_c = Task(func=lambda ctx: task_record(ctx, "C", 0.05), name="C")
    t_d = Task(func=lambda ctx: task_record(ctx, "D"), name="D")
    
    # A >> (B & C) >> D
    # Note: The DSL (B & C) returns a list, so we need to handle it manually or use DSL if available.
    # Let's use manual dependency setting for clarity in this test, or use the DSL if we trust it.
    # Using manual to be safe and focus on Engine.
    
    t_b.dependencies.add(t_a)
    t_c.dependencies.add(t_a)
    t_d.dependencies.add(t_b)
    t_d.dependencies.add(t_c)
    
    flow = Flow(name="diamond_flow")
    flow.add_task(t_a)
    flow.add_task(t_b)
    flow.add_task(t_c)
    flow.add_task(t_d)
    
    engine = Engine()
    start = time.time()
    ctx = engine.run(flow)
    duration = time.time() - start
    
    assert ctx.results["A"] == "A"
    assert ctx.results["B"] == "B"
    assert ctx.results["C"] == "C"
    assert ctx.results["D"] == "D"
    
    # Check order
    # A must be first
    assert results[0] == "A"
    # D must be last
    assert results[-1] == "D"
    # B and C are in middle (order between them doesn't matter)
    assert "B" in results[1:3]
    assert "C" in results[1:3]
    
    # Duration check: A(0) + max(B(0.05), C(0.05)) + D(0) ~= 0.05
    # If sequential: 0.1
    assert duration < 0.09
