import pytest

from pyoco.core.models import Task
from pyoco.dsl.graph import (
    GraphReferenceError,
    GraphValidationError,
    build_flow_from_graph,
    parse_graph,
    resolve_pipe_refs,
    validate_graph_terms,
)
from pyoco.dsl.nodes import ForEachNode


def _tasks(*names: str):
    return {name: Task(func=lambda: None, name=name) for name in names}


def test_build_flow_with_pipe_reference():
    tasks = _tasks("A", "B", "X", "C")
    flow = build_flow_from_graph(
        graph="A >> pipe(BX) >> C",
        pipes={"BX": "B >> X"},
        tasks=tasks,
        flow_name="main",
    )
    a = tasks["A"]
    b = tasks["B"]
    x = tasks["X"]
    c = tasks["C"]
    assert b in a.dependents
    assert x in b.dependents
    assert c in x.dependents


def test_resolve_pipe_reference_cycle():
    parsed = parse_graph("A >> pipe(BX)")
    with pytest.raises(GraphReferenceError):
        resolve_pipe_refs(parsed, pipes={"BX": "pipe(CX)", "CX": "pipe(BX)"})


def test_validate_switch_without_default_warns():
    parsed = parse_graph("switch(on={{k}}){ A: TaskA; }")
    report = validate_graph_terms(parsed)
    assert report.status == "warning"
    assert any("switch has no default case" in w for w in report.warnings)


def test_invalid_collect_mode_errors_on_build():
    tasks = _tasks("A")
    with pytest.raises(GraphValidationError):
        build_flow_from_graph(
            graph="repeat(count=1, collect=oops){ A }",
            tasks=tasks,
            flow_name="main",
        )


def test_foreach_index_alias_compiles_to_node():
    tasks = _tasks("A")
    flow = build_flow_from_graph(
        graph="foreach(over={{items}}, item=it, index=i){ A }",
        tasks=tasks,
        flow_name="main",
    )
    node = flow.build_program().steps[0]
    assert isinstance(node, ForEachNode)
    assert node.alias == "it"
    assert node.index_alias == "i"
    assert node.collect == "list"

