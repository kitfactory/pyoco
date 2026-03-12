from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Pipeline:
    terms: List["Term"] = field(default_factory=list)


class Term:
    pass


@dataclass
class TaskTerm(Term):
    name: str
    node_name: Optional[str] = None


@dataclass
class PipeRefTerm(Term):
    name: str


@dataclass
class SwitchCase:
    value: str
    branch: Pipeline


@dataclass
class SwitchTerm(Term):
    on: str
    cases: List[SwitchCase] = field(default_factory=list)
    default: Optional[Pipeline] = None


@dataclass
class RepeatTerm(Term):
    count: str
    collect: Optional[str]
    body: Pipeline


@dataclass
class ForEachTerm(Term):
    over: str
    item: Optional[str]
    index: Optional[str]
    collect: Optional[str]
    body: Pipeline


@dataclass
class UntilTerm(Term):
    cond: str
    max_iter: Optional[str]
    collect: Optional[str]
    body: Pipeline


@dataclass
class GraphValidationReport:
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        return "ok"

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
