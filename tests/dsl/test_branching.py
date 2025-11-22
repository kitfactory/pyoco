import pytest
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine
from pyoco.dsl.syntax import task, Branch

def test_dsl_branching_syntax():
    @task
    def A(ctx): return "A"
    @task
    def B(ctx): return "B"
    @task
    def C(ctx): return "C"
    
    # (A | B) >> C
    # A | B returns Branch([A, B])
    # Branch >> C sets C.trigger_policy = "ANY" and adds deps
    
    branch = (A | B)
    assert isinstance(branch, Branch)
    assert len(branch) == 2
    
    branch >> C
    
    assert C.task.trigger_policy == "ANY"
    assert A.task in C.task.dependencies
    assert B.task in C.task.dependencies

def test_engine_or_join():
    # A (success) | B (fail) >> C
    # C should run because A succeeded
    
    def task_a(): return "A"
    def task_b(): raise ValueError("Fail")
    def task_c(): return "C"
    
    t_a = Task(func=task_a, name="A")
    t_b = Task(func=task_b, name="B", fail_policy="isolate") # Isolate so flow continues
    t_c = Task(func=task_c, name="C", trigger_policy="ANY")
    
    # Manually link
    t_c.dependencies.add(t_a)
    t_c.dependencies.add(t_b)
    
    flow = Flow()
    flow.add_task(t_a)
    flow.add_task(t_b)
    flow.add_task(t_c)
    
    engine = Engine()
    ctx = engine.run(flow)
    
    assert ctx.results["C"] == "C"
    assert ctx.results["A"] == "A"
    assert "B" not in ctx.results # Failed
