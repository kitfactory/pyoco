import pytest
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine
from pyoco.core.context import Context

def test_task_execution():
    def func(ctx, x):
        return x + 1
    
    t = Task(func=func, name="t")
    # Engine handles execution, not Task directly
    engine = Engine()
    ctx = Context(params={"x": 1})
    # We need a flow to run
    flow = Flow()
    flow.add_task(t)
    
    res_ctx = engine.run(flow, params={"x": 1})
    assert res_ctx.results["t"] == 2

def test_dependency_chaining():
    t1 = Task(lambda: 1, name="t1")
    t2 = Task(lambda: 2, name="t2")
    
    t1.dependents.add(t2)
    t2.dependencies.add(t1)
    
    assert t1 in t2.dependencies
    assert t2 in t1.dependents

def test_workflow_execution(capsys):
    flow = Flow("test")
    
    t1 = Task(lambda: print("t1"), name="t1")
    t2 = Task(lambda: print("t2"), name="t2")
    
    # Manual linking
    t1.dependents.add(t2)
    t2.dependencies.add(t1)
    
    flow.add_task(t1)
    flow.add_task(t2)
    
    engine = Engine()
    engine.run(flow)
    
    captured = capsys.readouterr()
    # Trace output
    assert "start node=t1" in captured.out or "start node=t1" in captured.err
    assert "start node=t2" in captured.out or "start node=t2" in captured.err
