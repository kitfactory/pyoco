from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Union


class ExpressionSyntaxError(ValueError):
    pass


class ExpressionEvaluationError(RuntimeError):
    pass


DOT_PATH_RE = re.compile(r"^[A-Za-z_][\w.]*$")


@dataclass(frozen=True)
class Expression:
    source: str
    _python: str = field(init=False, repr=False)
    _code: object = field(init=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.source, str):
            raise TypeError("Expression source must be a string.")
        python_expr = translate(self.source)
        object.__setattr__(self, "_python", python_expr)
        object.__setattr__(self, "_code", compile_safely(python_expr))

    def evaluate(
        self,
        ctx: Optional[Mapping[str, Any]] = None,
        env: Optional[Mapping[str, Any]] = None,
        extras: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        scope = build_eval_scope(ctx or {}, env or {}, extras or {})
        try:
            return eval(self._code, {"__builtins__": {}}, scope)  # noqa: S307
        except Exception as exc:
            raise ExpressionEvaluationError(
                f"Failed to evaluate expression '{self.source}': {exc}"
            ) from exc


def ensure_expression(value: Union[str, Expression]) -> Expression:
    if isinstance(value, Expression):
        return value
    if isinstance(value, str):
        return Expression(value.strip())
    raise TypeError(f"Unsupported expression value: {value!r}")


def translate(expr: str) -> str:
    if "_ctx" in expr or "_env" in expr:
        raise ExpressionSyntaxError("Use $ctx/$env references instead of _ctx/_env.")
    def replace_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("$ctx."):
            path = token[len("$ctx.") :]
            return f"_ctx('{path}')"
        if token.startswith("$env."):
            path = token[len("$env.") :]
            return f"_env('{path}')"
        raise ExpressionSyntaxError(f"Unsupported token '{token}'")

    token_re = re.compile(r"\$(?:ctx|env)\.[A-Za-z_][\w.]*")
    translated = token_re.sub(replace_token, expr.strip())
    if "$" in translated:
        raise ExpressionSyntaxError("All references must use $ctx.xxx or $env.xxx form.")
    return translated


ALLOWED_NODES = {
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Gt,
    ast.GtE,
    ast.Lt,
    ast.LtE,
    ast.In,
    ast.NotIn,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Call,
}


def compile_safely(python_expr: str):
    try:
        tree = ast.parse(python_expr, mode="eval")
    except SyntaxError as exc:
        raise ExpressionSyntaxError(str(exc)) from exc

    for node in ast.walk(tree):
        if not isinstance(node, tuple(ALLOWED_NODES)):
            raise ExpressionSyntaxError(f"Unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in {"_ctx", "_env"}:
            raise ExpressionSyntaxError(f"Unknown identifier '{node.id}' in expression.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in {"_ctx", "_env"}:
                raise ExpressionSyntaxError("Only $ctx/$env references are allowed.")
            if len(node.args) != 1 or not isinstance(node.args[0], ast.Constant):
                raise ExpressionSyntaxError("Context references must be constant strings.")
    return compile(tree, "<expression>", "eval")


def build_eval_scope(
    ctx: Mapping[str, Any], env: Mapping[str, Any], extras: Mapping[str, Any]
) -> Dict[str, Callable[[str], Any]]:
    scope = {
        "_ctx": lambda path: resolve_path(ctx, path, "$ctx"),
        "_env": lambda path: resolve_path(env, path, "$env"),
    }
    scope.update(extras)
    return scope


def resolve_path(data: Mapping[str, Any], path: str, root: str):
    if not DOT_PATH_RE.match(path):
        raise ExpressionEvaluationError(f"Invalid path '{path}' for {root}.")
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, Mapping):
            if part not in current:
                raise ExpressionEvaluationError(f"{root}.{path} not found.")
            current = current[part]
        else:
            if not hasattr(current, part):
                raise ExpressionEvaluationError(f"{root}.{path} not found.")
            current = getattr(current, part)
    return current


__all__ = [
    "Expression",
    "ensure_expression",
    "ExpressionSyntaxError",
    "ExpressionEvaluationError",
]
