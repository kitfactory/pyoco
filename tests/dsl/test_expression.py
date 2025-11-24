import pytest

from pyoco.dsl.expressions import (
    Expression,
    ExpressionEvaluationError,
    ExpressionSyntaxError,
)


def test_expression_evaluates_ctx_and_env():
    expr = Expression("$ctx.value > 5 and $env.mode == 'prod'")
    result = expr.evaluate(ctx={"value": 10}, env={"mode": "prod"})
    assert result is True


def test_expression_translation_errors_on_unknown_tokens():
    with pytest.raises(ExpressionSyntaxError):
        Expression("$unknown.foo")


def test_expression_missing_path_raises_evaluation_error():
    expr = Expression("$ctx.value")
    with pytest.raises(ExpressionEvaluationError):
        expr.evaluate(ctx={})


def test_expression_disallows_calling_functions():
    with pytest.raises(ExpressionSyntaxError):
        Expression("_ctx('value')")
