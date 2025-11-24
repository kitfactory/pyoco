from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..core.models import Flow
from .nodes import (
    CaseNode,
    ForEachNode,
    RepeatNode,
    SubFlowNode,
    SwitchNode,
    TaskNode,
    UntilNode,
    DSLNode,
    DEFAULT_CASE_VALUE,
)


@dataclass
class ValidationReport:
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        return "ok"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class FlowValidator:
    """
    Traverses a Flow's SubFlow definition and produces warnings/errors for
    problematic control-flow constructs (unbounded loops, duplicate cases, etc.).
    """

    def __init__(self, flow: Flow):
        self.flow = flow
        self.report = ValidationReport()

    def validate(self) -> ValidationReport:
        program = self.flow.build_program()
        self._visit_subflow(program, "flow")
        return self.report

    # Traversal helpers --------------------------------------------------
    def _visit_subflow(self, subflow: SubFlowNode, path: str):
        for idx, node in enumerate(subflow.steps):
            self._visit_node(node, f"{path}.step[{idx}]")

    def _visit_node(self, node: DSLNode, path: str):
        if isinstance(node, TaskNode):
            return
        if isinstance(node, RepeatNode):
            self._visit_subflow(node.body, f"{path}.repeat")
        elif isinstance(node, ForEachNode):
            self._visit_subflow(node.body, f"{path}.foreach")
        elif isinstance(node, UntilNode):
            self._validate_until(node, path)
            self._visit_subflow(node.body, f"{path}.until")
        elif isinstance(node, SwitchNode):
            self._validate_switch(node, path)
        elif isinstance(node, SubFlowNode):
            self._visit_subflow(node, path)
        else:
            self.report.errors.append(f"{path}: Unknown node type {type(node).__name__}")

    # Validators ---------------------------------------------------------
    def _validate_until(self, node: UntilNode, path: str):
        if node.max_iter is None:
            self.report.warnings.append(f"{path}: Until loop missing max_iter (defaults to 1000).")

    def _validate_switch(self, node: SwitchNode, path: str):
        seen_values = set()
        default_count = 0
        for idx, case in enumerate(node.cases):
            case_path = f"{path}.case[{idx}]"
            if case.value == DEFAULT_CASE_VALUE:
                default_count += 1
                if default_count > 1:
                    self.report.errors.append(f"{case_path}: Multiple default (*) cases are not allowed.")
            else:
                try:
                    key = case.value
                    if key in seen_values:
                        self.report.errors.append(f"{case_path}: Duplicate switch value '{case.value}'.")
                    else:
                        seen_values.add(key)
                except TypeError:
                    self.report.errors.append(f"{case_path}: Unhashable switch value '{case.value}'.")
            self._visit_subflow(case.target, f"{case_path}.target")

        if default_count == 0:
            self.report.warnings.append(f"{path}: Switch has no default (*) case.")
