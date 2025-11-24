import pytest

from pyoco import Flow, task
from pyoco.core.engine import Engine
from pyoco.core.exceptions import UntilMaxIterationsExceeded


def test_repeat_loop_runs_body_fixed_times():
    events = []

    @task
    def seed(ctx):
        ctx.set_var("value", 0)

    @task
    def increment(ctx):
        current = ctx.get_var("value")
        ctx.set_var("value", current + 1)
        events.append(current + 1)
        return current + 1

    flow = Flow("repeat_loop")
    flow >> seed >> (increment)[3]

    engine = Engine()
    ctx = engine.run(flow)

    assert events == [1, 2, 3]
    assert ctx.get_var("value") == 3


def test_foreach_loop_iterates_sequence_and_alias():
    seen = []

    @task
    def seed(ctx):
        ctx.set_var("items", [10, 20, 30])

    @task
    def record(ctx):
        seen.append((ctx.loop.index, ctx.loop.item, ctx.get_var("item")))
        return ctx.loop.item

    flow = Flow("foreach_loop")
    flow >> seed >> (record)["$ctx.items as item"]

    engine = Engine()
    ctx = engine.run(flow)

    assert seen == [(0, 10, 10), (1, 20, 20), (2, 30, 30)]
    assert ctx.get_var("item") is None


def test_until_loop_stops_on_condition():
    @task
    def init(ctx):
        ctx.set_var("value", 0)

    @task
    def bump(ctx):
        current = ctx.get_var("value")
        ctx.set_var("value", current + 1)
        return current + 1

    flow = Flow("until_loop")
    flow >> init >> (bump) % ("$ctx.results.bump >= 3", 10)

    engine = Engine()
    ctx = engine.run(flow)

    assert ctx.get_var("value") == 3
    assert ctx.results["bump"] == 3


def test_until_loop_respects_max_iter():
    @task
    def init(ctx):
        ctx.set_var("value", 0)

    @task
    def bump(ctx):
        current = ctx.get_var("value")
        ctx.set_var("value", current + 1)
        return current + 1

    flow = Flow("until_loop_max")
    flow >> init >> (bump) % ("$ctx.results.bump >= 5", 2)

    engine = Engine()
    with pytest.raises(UntilMaxIterationsExceeded):
        engine.run(flow)
