from pyoco import Flow, task
from pyoco.core.engine import Engine
from pyoco.dsl.syntax import switch


def test_switch_executes_matching_case():
    events = []

    @task
    def branch_x(ctx):
        events.append("X")

    @task
    def branch_y(ctx):
        events.append("Y")

    @task
    def default_branch(ctx):
        events.append("default")

    flow = Flow("switch_flow")
    flow >> switch("$ctx.params.flag")[("X" >> branch_x, "Y" >> branch_y, "*" >> default_branch)]

    engine = Engine()
    engine.run(flow, params={"flag": "Y"})

    assert events == ["Y"]


def test_switch_falls_back_to_default():
    events = []

    @task
    def branch_a(ctx):
        events.append("A")

    @task
    def default_branch(ctx):
        events.append("default")

    flow = Flow("switch_default")
    flow >> switch("$ctx.params.flag")[("A" >> branch_a, "*" >> default_branch)]

    engine = Engine()
    engine.run(flow, params={"flag": "Z"})

    assert events == ["default"]
