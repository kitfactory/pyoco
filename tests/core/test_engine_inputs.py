import pytest
from pyoco.core.models import Task, Flow
from pyoco.core.engine import Engine
from pyoco.core.context import Context

def task_a(ctx):
    return 10

def task_b(x):
    return x * 2

def task_c(val, other):
    return val + other

def test_engine_inputs_injection():
    # Task A: returns 10
    t_a = Task(func=task_a, name="A")
    
    # Task B: takes x, input mapped from A's output
    t_b = Task(func=task_b, name="B")
    t_b.inputs = {"x": "$node.A.output"}
    
    # Flow: A >> B
    flow = Flow(name="test_flow")
    flow >> t_a >> t_b
    
    engine = Engine()
    ctx = engine.run(flow)
    
    assert ctx.results["A"] == 10
    assert ctx.results["B"] == 20

def test_engine_inputs_params_and_env(monkeypatch):
    monkeypatch.setenv("MY_ENV_VAR", "5")
    
    t_c = Task(func=task_c, name="C")
    t_c.inputs = {
        "val": "$ctx.params.start_val",
        "other": "$env.MY_ENV_VAR" # String "5", but wait, env vars are strings. 
                                   # If we want int, we might need casting or the task handles it.
                                   # Let's assume task handles string or we pass int in params.
    }
    # Let's adjust task_c to handle string if needed, or just test string concat if that's easier.
    # But here x*2 in task_b implies int.
    # Let's change task_c to int conversion for safety in this test
    def task_c_safe(val, other):
        return int(val) + int(other)
    t_c.func = task_c_safe
    
    flow = Flow(name="test_flow_2")
    flow.add_task(t_c)
    
    engine = Engine()
    # params: start_val = 10
    ctx = engine.run(flow, params={"start_val": 10})
    
    # 10 + 5 = 15
    assert ctx.results["C"] == 15

def test_engine_mixed_injection():
    # Test mixing implicit ctx injection and explicit inputs
    def task_mixed(ctx, y):
        return ctx.params["base"] + y
    
    t = Task(func=task_mixed, name="Mixed")
    t.inputs = {"y": 5}
    
    flow = Flow()
    flow.add_task(t)
    
    engine = Engine()
    ctx = engine.run(flow, params={"base": 100})
    
    assert ctx.results["Mixed"] == 105
