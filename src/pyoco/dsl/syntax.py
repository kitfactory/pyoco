from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple, Union

from ..core.models import Task
from .expressions import Expression, ensure_expression
from .nodes import (
    CaseNode,
    DSLNode,
    ForEachNode,
    RepeatNode,
    SubFlowNode,
    SwitchNode,
    TaskNode,
    UntilNode,
    DEFAULT_CASE_VALUE,
)
RESERVED_CTX_KEYS = {"params", "results", "scratch", "loop", "loops", "env", "artifacts"}


class FlowFragment:
    """
    Represents a fragment of a flow (sequence of DSL nodes). Every DSL
    operator returns a FlowFragment so sub-flows can be composed before
    being attached to a Flow.
    """

    __slots__ = ("_nodes",)

    def __init__(self, nodes: Sequence[DSLNode]):
        if not isinstance(nodes, (list, tuple)):
            raise TypeError("FlowFragment expects a list/tuple of nodes.")
        self._nodes: Tuple[DSLNode, ...] = tuple(nodes)

    # Sequence composition -------------------------------------------------
    def __rshift__(self, other: Union["FlowFragment", "TaskWrapper", Task]) -> "FlowFragment":
        right = ensure_fragment(other)
        self._link_to(right)
        return FlowFragment(self._nodes + right._nodes)

    # Loop support ---------------------------------------------------------
    def __getitem__(self, selector: Union[int, str, Expression]) -> "FlowFragment":
        """
        Implements [] operator for repeat / for-each loops.
        """

        body = self.to_subflow()
        if isinstance(selector, int):
            if selector < 0:
                raise ValueError("Repeat count must be non-negative.")
            node = RepeatNode(body=body, count=selector)
            return FlowFragment([node])

        if isinstance(selector, Expression):
            node = RepeatNode(body=body, count=selector)
            return FlowFragment([node])

        if isinstance(selector, str):
            source, alias = parse_foreach_selector(selector)
            node = ForEachNode(body=body, source=ensure_expression(source), alias=alias)
            return FlowFragment([node])

        raise TypeError(f"Unsupported loop selector: {selector!r}")

    def __mod__(self, value: Union[str, Expression, Tuple[Union[str, Expression], int]]) -> "FlowFragment":
        """
        Implements the % operator for until loops.
        """

        max_iter = None
        expr_value: Union[str, Expression]

        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError("Until tuple selector must be (expression, max_iter).")
            expr_value, max_iter = value
        else:
            expr_value = value

        node = UntilNode(
            body=self.to_subflow(),
            condition=ensure_expression(expr_value),
            max_iter=max_iter,
        )
        return FlowFragment([node])

    # Switch/case ----------------------------------------------------------
    def __rrshift__(self, other: Union[str, int, float, bool]) -> CaseNode:
        """
        Enables `"X" >> fragment` syntax by reversing the operands.
        """

        if isinstance(other, str) and other == "*":
            value = DEFAULT_CASE_VALUE
        else:
            value = other
        return CaseNode(value=value, target=self.to_subflow())

    # Helpers --------------------------------------------------------------
    def to_subflow(self) -> SubFlowNode:
        return SubFlowNode(list(self._nodes))

    def task_nodes(self) -> List[Task]:
        tasks: List[Task] = []
        for node in self._nodes:
            tasks.extend(_collect_tasks(node))
        return tasks

    def _first_task(self) -> Task | None:
        for node in self._nodes:
            tasks = _collect_tasks(node)
            if tasks:
                return tasks[0]
        return None

    def _last_task(self) -> Task | None:
        for node in reversed(self._nodes):
            tasks = _collect_tasks(node)
            if tasks:
                return tasks[-1]
        return None

    def _link_to(self, other: "FlowFragment"):
        left_task = self._last_task()
        right_task = other._first_task()
        if left_task and right_task and left_task is not right_task:
            right_task.dependencies.add(left_task)
            left_task.dependents.add(right_task)

    def has_control_flow(self) -> bool:
        return any(not isinstance(node, TaskNode) for node in self._nodes)


class TaskWrapper(FlowFragment):
    """
    Wraps a Task to handle DSL operators, while exposing the underlying
    task for legacy access (e.g., `task.task.inputs = ...`).
    """

    __slots__ = ("task",)

    def __init__(self, task: Task):
        self.task = task
        super().__init__([TaskNode(task)])

    def __call__(self, *args, **kwargs) -> "TaskWrapper":
        return self

    def __and__(self, other):
        return Parallel([self, other])

    def __or__(self, other):
        return Branch([self, other])


class Branch(list):
    """Represents `A | B` OR-branches (legacy)."""

    def __rshift__(self, other):
        targets = _collect_target_tasks(other)
        for target in targets:
            target.trigger_policy = "ANY"
            for source in self:
                if hasattr(source, "task"):
                    target.dependencies.add(source.task)
                    source.task.dependents.add(target)
        return other


class Parallel(list):
    """Represents `A & B` parallel branches (legacy)."""

    def __rshift__(self, other):
        targets = _collect_target_tasks(other)
        for target in targets:
            for source in self:
                if hasattr(source, "task"):
                    target.dependencies.add(source.task)
                    source.task.dependents.add(target)
        return other


def switch(expression: Union[str, Expression]) -> "SwitchBuilder":
    return SwitchBuilder(expression=ensure_expression(expression))


@dataclass
class SwitchBuilder:
    expression: Expression

    def __getitem__(self, cases: Union[CaseNode, Sequence[CaseNode]]) -> FlowFragment:
        if isinstance(cases, CaseNode):
            case_list = [cases]
        elif isinstance(cases, Sequence):
            case_list = list(cases)
        else:
            raise TypeError("switch()[...] expects CaseNode(s)")

        if not case_list:
            raise ValueError("switch() requires at least one case.")
        return FlowFragment([SwitchNode(expression=self.expression, cases=case_list)])


# Helper utilities ---------------------------------------------------------
def ensure_fragment(value: Union[FlowFragment, TaskWrapper, Task]) -> FlowFragment:
    if isinstance(value, FlowFragment):
        return value
    if isinstance(value, TaskWrapper):
        return value
    if hasattr(value, "task"):
        return FlowFragment([TaskNode(value.task)])
    if isinstance(value, Task):
        return TaskWrapper(value)
    raise TypeError(f"Cannot treat {value!r} as a flow fragment.")


def parse_foreach_selector(selector: str) -> Tuple[str, Union[str, None]]:
    token = selector.strip()
    alias = None
    if " as " in token:
        expr, alias = token.split(" as ", 1)
        token = expr.strip()
        alias = alias.strip()
        if not alias or not alias.isidentifier() or alias in RESERVED_CTX_KEYS:
            raise ValueError(f"Invalid foreach alias '{alias}'.")

    return token, alias


def _collect_tasks(obj) -> List[Task]:
    if isinstance(obj, TaskNode):
        return [obj.task]
    if isinstance(obj, SubFlowNode):
        tasks: List[Task] = []
        for step in obj.steps:
            tasks.extend(_collect_tasks(step))
        return tasks
    if isinstance(obj, RepeatNode):
        return _collect_tasks(obj.body)
    if isinstance(obj, ForEachNode):
        return _collect_tasks(obj.body)
    if isinstance(obj, UntilNode):
        return _collect_tasks(obj.body)
    if isinstance(obj, SwitchNode):
        tasks: List[Task] = []
        for case in obj.cases:
            tasks.extend(_collect_tasks(case.target))
        return tasks
    return []


def _collect_target_tasks(other) -> List[Task]:
    targets = []
    if hasattr(other, "task"):
        targets = [other.task]
    elif isinstance(other, (list, tuple)):
        for item in other:
            if hasattr(item, "task"):
                targets.append(item.task)
    return targets


def task(func: Callable) -> TaskWrapper:
    return TaskWrapper(Task(func=func, name=func.__name__))


__all__ = ["task", "FlowFragment", "switch", "TaskWrapper", "Branch", "Parallel"]
