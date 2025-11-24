import pytest

from pyoco.core.engine import Engine
from pyoco.core.models import Flow
from pyoco.dsl.syntax import switch, task
from pyoco.dsl.validator import FlowValidator
from pyoco.core.exceptions import UntilMaxIterationsExceeded


def test_validator_warns_on_until_without_max():
    events = []

    @task
    def start(ctx):
        events.append("start")

    flow = Flow("warn_until")
    flow >> (start) % "$ctx.loop.iteration > 1"

    report = FlowValidator(flow).validate()
    assert any("missing max_iter" in warning for warning in report.warnings)


def test_validator_errors_on_duplicate_switch_cases():
    @task
    def branch_a(ctx):
        return "A"

    flow = Flow("dup_switch")
    flow >> switch("$ctx.params.flag")[("X" >> branch_a, "X" >> branch_a)]

    report = FlowValidator(flow).validate()
    assert report.status == "error"
    assert any("Duplicate switch value" in err for err in report.errors)


def test_validator_errors_on_multiple_default_cases():
    @task
    def branch_a(ctx):
        return "A"

    flow = Flow("dup_default")
    flow >> switch("$ctx.params.flag")[("*" >> branch_a, "*" >> branch_a)]

    report = FlowValidator(flow).validate()
    assert any("Multiple default" in err for err in report.errors)
