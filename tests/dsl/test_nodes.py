import pytest

from pyoco.dsl.syntax import switch, task
from pyoco.dsl.nodes import (
    ForEachNode,
    RepeatNode,
    SwitchNode,
    TaskNode,
    UntilNode,
)


def build_two_tasks():
    @task
    def alpha(ctx):  # pragma: no cover - body unused
        return "alpha"

    @task
    def beta(ctx):  # pragma: no cover - body unused
        return "beta"

    return alpha, beta


def test_task_chaining_creates_sequence():
    t1, t2 = build_two_tasks()
    fragment = t1 >> t2
    subflow = fragment.to_subflow()
    assert len(subflow.steps) == 2
    assert isinstance(subflow.steps[0], TaskNode)
    assert isinstance(subflow.steps[1], TaskNode)


def test_repeat_loop_builds_repeat_node():
    t1, t2 = build_two_tasks()
    loop_fragment = (t1 >> t2)[3]
    subflow = loop_fragment.to_subflow()
    assert len(subflow.steps) == 1
    loop_node = subflow.steps[0]
    assert isinstance(loop_node, RepeatNode)
    assert loop_node.count == 3
    assert len(loop_node.body.steps) == 2


def test_foreach_loop_parses_alias():
    t1, t2 = build_two_tasks()
    fragment = (t1 >> t2)["$ctx.items as item"]
    foreach = fragment.to_subflow().steps[0]
    assert isinstance(foreach, ForEachNode)
    assert foreach.alias == "item"
    assert foreach.source.source == "$ctx.items"


def test_until_loop_supports_tuple_selector():
    t1, t2 = build_two_tasks()
    until_fragment = (t1 >> t2) % ("$ctx.metrics.acc > 0.9", 10)
    until = until_fragment.to_subflow().steps[0]
    assert isinstance(until, UntilNode)
    assert until.max_iter == 10
    assert until.condition.source == "$ctx.metrics.acc > 0.9"


def test_switch_builder_collects_cases():
    t1, t2 = build_two_tasks()
    fragment = switch("$ctx.status")[("X" >> t1, "*" >> t2)]
    switch_node = fragment.to_subflow().steps[0]
    assert isinstance(switch_node, SwitchNode)
    assert len(switch_node.cases) == 2
    assert switch_node.cases[0].value == "X"
    assert switch_node.cases[1].value == "__default__"
