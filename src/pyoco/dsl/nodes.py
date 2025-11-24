from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence as TypingSequence, Union

from ..core.models import Task
from .expressions import Expression, ensure_expression


DEFAULT_CASE_VALUE = "__default__"


class DSLNode:
    """Base class for all DSL AST nodes."""


@dataclass
class TaskNode(DSLNode):
    task: Task


@dataclass
class SubFlowNode(DSLNode):
    steps: List[DSLNode] = field(default_factory=list)


@dataclass
class RepeatNode(DSLNode):
    body: SubFlowNode
    count: Union[int, Expression]


@dataclass
class ForEachNode(DSLNode):
    body: SubFlowNode
    source: Expression
    alias: Optional[str] = None


@dataclass
class UntilNode(DSLNode):
    body: SubFlowNode
    condition: Expression
    max_iter: Optional[int] = None


@dataclass
class CaseNode(DSLNode):
    value: Union[str, int, float, bool]
    target: SubFlowNode


@dataclass
class SwitchNode(DSLNode):
    expression: Expression
    cases: List[CaseNode] = field(default_factory=list)
