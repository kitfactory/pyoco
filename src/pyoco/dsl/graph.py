from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..core.models import Flow, Task
from .expressions import ensure_expression
from .nodes import (
    CaseNode,
    DEFAULT_CASE_VALUE,
    ForEachNode,
    RepeatNode,
    SwitchNode,
    UntilNode,
)
from .syntax import FlowFragment, TaskWrapper


MAX_PIPE_EXPANSION_DEPTH = 128
MAX_PIPE_EXPANDED_TERMS = 4096
ALLOWED_COLLECT_MODES = {"list", "last", "first", "flatten"}
IDENT_RE = re.compile(r"^[A-Za-z_]\w*$")
PATH_RE = re.compile(r"^[A-Za-z_][\w.]*$")


class GraphSyntaxError(ValueError):
    pass


class GraphReferenceError(ValueError):
    pass


class GraphValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    pos: int


@dataclass
class Pipeline:
    terms: List["Term"] = field(default_factory=list)


class Term:
    pass


@dataclass
class TaskTerm(Term):
    name: str


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


class GraphLexer:
    def __init__(self, text: str):
        self.text = text
        self.length = len(text)
        self.pos = 0

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch in " \t\r\n":
                self.pos += 1
                continue
            if ch == "#":
                self._skip_comment()
                continue
            if self._peek(">>"):
                tokens.append(Token("SHIFT", ">>", self.pos))
                self.pos += 2
                continue
            if ch == ">":
                raise GraphSyntaxError(
                    f"Unsupported operator '>' at position {self.pos}. Use '>>' only."
                )
            if self._peek("{{"):
                tokens.append(self._read_template())
                continue
            if ch in ("'", '"'):
                tokens.append(self._read_string(ch))
                continue
            if ch.isdigit():
                tokens.append(self._read_number())
                continue
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier())
                continue
            punct = {
                "(": "LPAREN",
                ")": "RPAREN",
                "{": "LBRACE",
                "}": "RBRACE",
                ":": "COLON",
                ";": "SEMI",
                ",": "COMMA",
                "=": "EQUAL",
            }
            kind = punct.get(ch)
            if kind:
                tokens.append(Token(kind, ch, self.pos))
                self.pos += 1
                continue
            raise GraphSyntaxError(f"Unexpected character '{ch}' at position {self.pos}.")
        tokens.append(Token("EOF", "", self.pos))
        return tokens

    def _peek(self, pat: str) -> bool:
        return self.text.startswith(pat, self.pos)

    def _skip_comment(self):
        while self.pos < self.length and self.text[self.pos] != "\n":
            self.pos += 1

    def _read_template(self) -> Token:
        start = self.pos
        self.pos += 2
        end = self.text.find("}}", self.pos)
        if end == -1:
            raise GraphSyntaxError(f"Unterminated template expression at position {start}.")
        body = self.text[self.pos:end].strip()
        self.pos = end + 2
        return Token("TEMPLATE", "{{" + body + "}}", start)

    def _read_string(self, quote: str) -> Token:
        start = self.pos
        self.pos += 1
        buf: List[str] = []
        escaped = False
        while self.pos < self.length:
            ch = self.text[self.pos]
            self.pos += 1
            if escaped:
                buf.append(ch)
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == quote:
                return Token("STRING", "".join(buf), start)
            buf.append(ch)
        raise GraphSyntaxError(f"Unterminated string at position {start}.")

    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < self.length and self.text[self.pos].isdigit():
            self.pos += 1
        return Token("NUMBER", self.text[start:self.pos], start)

    def _read_identifier(self) -> Token:
        start = self.pos
        self.pos += 1
        while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] == "_"):
            self.pos += 1
        return Token("IDENT", self.text[start:self.pos], start)


class GraphParser:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = list(tokens)
        self.idx = 0

    def parse(self) -> Pipeline:
        pipeline = self._parse_pipeline(stop_kinds={"EOF"})
        self._expect("EOF")
        return pipeline

    def _parse_pipeline(self, stop_kinds: Set[str]) -> Pipeline:
        if self._peek().kind in stop_kinds:
            raise GraphSyntaxError(f"Empty pipeline before token '{self._peek().kind}'.")
        terms: List[Term] = [self._parse_term()]
        while self._peek().kind == "SHIFT":
            self._advance()
            terms.append(self._parse_term())
        if self._peek().kind not in stop_kinds:
            token = self._peek()
            raise GraphSyntaxError(
                f"Expected one of {sorted(stop_kinds)} but got '{token.kind}' at position {token.pos}."
            )
        return Pipeline(terms=terms)

    def _parse_term(self) -> Term:
        token = self._peek()
        if token.kind != "IDENT":
            raise GraphSyntaxError(f"Expected term at position {token.pos}, got '{token.kind}'.")
        ident = token.value
        if self._peek(1).kind == "LPAREN":
            if ident == "pipe":
                return self._parse_pipe_ref()
            if ident == "switch":
                return self._parse_switch()
            if ident == "repeat":
                return self._parse_repeat()
            if ident == "foreach":
                return self._parse_foreach()
            if ident == "until":
                return self._parse_until()
            raise GraphSyntaxError(f"Unknown callable term '{ident}' at position {token.pos}.")
        self._advance()
        return TaskTerm(name=ident)

    def _parse_pipe_ref(self) -> PipeRefTerm:
        self._expect_ident("pipe")
        self._expect("LPAREN")
        name_tok = self._expect_any({"IDENT", "STRING"})
        self._expect("RPAREN")
        return PipeRefTerm(name=name_tok.value)

    def _parse_switch(self) -> SwitchTerm:
        self._expect_ident("switch")
        args = self._parse_named_args()
        on = args.get("on")
        if not on:
            raise GraphSyntaxError("switch(...) requires 'on='.")
        self._expect("LBRACE")
        cases: List[SwitchCase] = []
        default_branch: Optional[Pipeline] = None
        while self._peek().kind != "RBRACE":
            if self._peek().kind == "SEMI":
                self._advance()
                continue
            if self._peek().kind == "IDENT" and self._peek().value == "default":
                self._advance()
                self._expect("COLON")
                default_branch = self._parse_branch({"SEMI", "RBRACE"})
            else:
                case_key = self._expect_any({"IDENT", "STRING", "NUMBER", "TEMPLATE"})
                self._expect("COLON")
                branch = self._parse_branch({"SEMI", "RBRACE"})
                cases.append(SwitchCase(value=case_key.value, branch=branch))
            if self._peek().kind == "SEMI":
                self._advance()
        self._expect("RBRACE")
        return SwitchTerm(on=on, cases=cases, default=default_branch)

    def _parse_repeat(self) -> RepeatTerm:
        self._expect_ident("repeat")
        args = self._parse_named_args()
        count = args.get("count")
        if not count:
            raise GraphSyntaxError("repeat(...) requires 'count='.")
        self._expect("LBRACE")
        body = self._parse_pipeline(stop_kinds={"RBRACE"})
        self._expect("RBRACE")
        return RepeatTerm(count=count, collect=args.get("collect"), body=body)

    def _parse_foreach(self) -> ForEachTerm:
        self._expect_ident("foreach")
        args = self._parse_named_args()
        over = args.get("over")
        if not over:
            raise GraphSyntaxError("foreach(...) requires 'over='.")
        self._expect("LBRACE")
        body = self._parse_pipeline(stop_kinds={"RBRACE"})
        self._expect("RBRACE")
        return ForEachTerm(
            over=over,
            item=args.get("item"),
            index=args.get("index"),
            collect=args.get("collect"),
            body=body,
        )

    def _parse_until(self) -> UntilTerm:
        self._expect_ident("until")
        args = self._parse_named_args()
        cond = args.get("cond")
        if not cond:
            raise GraphSyntaxError("until(...) requires 'cond='.")
        self._expect("LBRACE")
        body = self._parse_pipeline(stop_kinds={"RBRACE"})
        self._expect("RBRACE")
        return UntilTerm(
            cond=cond,
            max_iter=args.get("max_iter"),
            collect=args.get("collect"),
            body=body,
        )

    def _parse_named_args(self) -> Dict[str, str]:
        args: Dict[str, str] = {}
        self._expect("LPAREN")
        if self._peek().kind == "RPAREN":
            self._advance()
            return args
        while True:
            key = self._expect("IDENT").value
            self._expect("EQUAL")
            value = self._expect_any({"IDENT", "NUMBER", "STRING", "TEMPLATE"}).value
            args[key] = value
            if self._peek().kind == "COMMA":
                self._advance()
                continue
            break
        self._expect("RPAREN")
        return args

    def _parse_branch(self, stop_kinds: Set[str]) -> Pipeline:
        if self._peek().kind == "STRING" and self._peek(1).kind in stop_kinds:
            quoted = self._advance().value
            return parse_graph(quoted)
        return self._parse_pipeline(stop_kinds=stop_kinds)

    def _peek(self, offset: int = 0) -> Token:
        pos = self.idx + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]

    def _advance(self) -> Token:
        token = self._peek()
        self.idx += 1
        return token

    def _expect(self, kind: str) -> Token:
        token = self._peek()
        if token.kind != kind:
            raise GraphSyntaxError(
                f"Expected '{kind}' at position {token.pos}, got '{token.kind}'."
            )
        self.idx += 1
        return token

    def _expect_ident(self, value: str):
        token = self._expect("IDENT")
        if token.value != value:
            raise GraphSyntaxError(
                f"Expected '{value}' at position {token.pos}, got '{token.value}'."
            )

    def _expect_any(self, kinds: Iterable[str]) -> Token:
        allowed = set(kinds)
        token = self._peek()
        if token.kind not in allowed:
            raise GraphSyntaxError(
                f"Expected one of {sorted(allowed)} at position {token.pos}, got '{token.kind}'."
            )
        self.idx += 1
        return token


def tokenize_graph(graph: str) -> List[Token]:
    return GraphLexer(graph).tokenize()


def parse_graph(graph: str) -> Pipeline:
    return GraphParser(tokenize_graph(graph)).parse()


def resolve_pipe_refs(
    pipeline: Pipeline,
    pipes: Optional[Dict[str, str]] = None,
    *,
    max_depth: int = MAX_PIPE_EXPANSION_DEPTH,
    max_terms: int = MAX_PIPE_EXPANDED_TERMS,
) -> Pipeline:
    resolved, _ = _resolve_pipeline(
        pipeline,
        pipes or {},
        stack=(),
        depth=0,
        term_budget=max_terms,
        max_depth=max_depth,
    )
    return resolved


def _resolve_pipeline(
    pipeline: Pipeline,
    pipes: Dict[str, str],
    *,
    stack: Tuple[str, ...],
    depth: int,
    term_budget: int,
    max_depth: int,
) -> Tuple[Pipeline, int]:
    terms: List[Term] = []
    remaining = term_budget
    for term in pipeline.terms:
        if isinstance(term, PipeRefTerm):
            name = term.name
            if name not in pipes:
                raise GraphReferenceError(f"Unknown pipe reference: {name}")
            if name in stack:
                cycle = " -> ".join(stack + (name,))
                raise GraphReferenceError(f"Cyclic pipe reference detected: {cycle}")
            if depth + 1 > max_depth:
                raise GraphReferenceError(f"Pipe expansion depth exceeded ({max_depth})")
            sub = parse_graph(pipes[name])
            expanded, remaining = _resolve_pipeline(
                sub,
                pipes,
                stack=stack + (name,),
                depth=depth + 1,
                term_budget=remaining,
                max_depth=max_depth,
            )
            terms.extend(expanded.terms)
            continue
        cloned = _resolve_term_children(
            term,
            pipes,
            stack=stack,
            depth=depth,
            term_budget=remaining,
            max_depth=max_depth,
        )
        terms.append(cloned.term)
        remaining = cloned.remaining_budget
        remaining -= _count_term(cloned.term)
        if remaining < 0:
            raise GraphReferenceError(f"Expanded terms exceeded limit ({MAX_PIPE_EXPANDED_TERMS})")
    return Pipeline(terms=terms), remaining


@dataclass
class _ResolvedTerm:
    term: Term
    remaining_budget: int


def _resolve_term_children(
    term: Term,
    pipes: Dict[str, str],
    *,
    stack: Tuple[str, ...],
    depth: int,
    term_budget: int,
    max_depth: int,
) -> _ResolvedTerm:
    if isinstance(term, SwitchTerm):
        remaining = term_budget
        cases: List[SwitchCase] = []
        for case in term.cases:
            resolved_branch, remaining = _resolve_pipeline(
                case.branch,
                pipes,
                stack=stack,
                depth=depth,
                term_budget=remaining,
                max_depth=max_depth,
            )
            cases.append(SwitchCase(value=case.value, branch=resolved_branch))
        default_branch = None
        if term.default is not None:
            default_branch, remaining = _resolve_pipeline(
                term.default,
                pipes,
                stack=stack,
                depth=depth,
                term_budget=remaining,
                max_depth=max_depth,
            )
        return _ResolvedTerm(
            SwitchTerm(on=term.on, cases=cases, default=default_branch),
            remaining,
        )
    if isinstance(term, RepeatTerm):
        resolved_body, remaining = _resolve_pipeline(
            term.body,
            pipes,
            stack=stack,
            depth=depth,
            term_budget=term_budget,
            max_depth=max_depth,
        )
        return _ResolvedTerm(
            RepeatTerm(count=term.count, collect=term.collect, body=resolved_body),
            remaining,
        )
    if isinstance(term, ForEachTerm):
        resolved_body, remaining = _resolve_pipeline(
            term.body,
            pipes,
            stack=stack,
            depth=depth,
            term_budget=term_budget,
            max_depth=max_depth,
        )
        return _ResolvedTerm(
            ForEachTerm(
                over=term.over,
                item=term.item,
                index=term.index,
                collect=term.collect,
                body=resolved_body,
            ),
            remaining,
        )
    if isinstance(term, UntilTerm):
        resolved_body, remaining = _resolve_pipeline(
            term.body,
            pipes,
            stack=stack,
            depth=depth,
            term_budget=term_budget,
            max_depth=max_depth,
        )
        return _ResolvedTerm(
            UntilTerm(
                cond=term.cond,
                max_iter=term.max_iter,
                collect=term.collect,
                body=resolved_body,
            ),
            remaining,
        )
    return _ResolvedTerm(term=term, remaining_budget=term_budget)


def _count_term(term: Term) -> int:
    if isinstance(term, SwitchTerm):
        count = 1
        for case in term.cases:
            count += sum(_count_term(t) for t in case.branch.terms)
        if term.default:
            count += sum(_count_term(t) for t in term.default.terms)
        return count
    if isinstance(term, (RepeatTerm, ForEachTerm, UntilTerm)):
        return 1 + sum(_count_term(t) for t in term.body.terms)
    return 1


def validate_graph_terms(pipeline: Pipeline) -> GraphValidationReport:
    report = GraphValidationReport()
    _validate_pipeline(pipeline, report, "flow")
    return report


def _validate_pipeline(pipeline: Pipeline, report: GraphValidationReport, path: str):
    for idx, term in enumerate(pipeline.terms):
        loc = f"{path}.term[{idx}]"
        if isinstance(term, SwitchTerm):
            seen: Set[str] = set()
            for case_idx, case in enumerate(term.cases):
                case_loc = f"{loc}.case[{case_idx}]"
                if case.value in seen:
                    report.errors.append(f"{case_loc}: duplicate switch case '{case.value}'.")
                seen.add(case.value)
                _validate_pipeline(case.branch, report, f"{case_loc}.branch")
            if term.default is None:
                report.warnings.append(f"{loc}: switch has no default case.")
            else:
                _validate_pipeline(term.default, report, f"{loc}.default")
            continue
        if isinstance(term, RepeatTerm):
            _validate_collect(loc, term.collect, "list", report)
            if term.count.isdigit() and int(term.count) < 0:
                report.errors.append(f"{loc}: repeat count must be non-negative.")
            _validate_pipeline(term.body, report, f"{loc}.body")
            continue
        if isinstance(term, ForEachTerm):
            _validate_collect(loc, term.collect, "list", report)
            _validate_identifier(loc, "item", term.item, report)
            _validate_identifier(loc, "index", term.index, report)
            _validate_pipeline(term.body, report, f"{loc}.body")
            continue
        if isinstance(term, UntilTerm):
            _validate_collect(loc, term.collect, "last", report)
            if term.max_iter is not None:
                if not term.max_iter.isdigit() or int(term.max_iter) < 1:
                    report.errors.append(f"{loc}: max_iter must be a positive integer.")
            _validate_pipeline(term.body, report, f"{loc}.body")
            continue


def _validate_collect(path: str, collect: Optional[str], default: str, report: GraphValidationReport):
    mode = collect or default
    if mode not in ALLOWED_COLLECT_MODES:
        report.errors.append(f"{path}: unsupported collect mode '{mode}'.")


def _validate_identifier(path: str, key: str, value: Optional[str], report: GraphValidationReport):
    if value is None:
        return
    if not IDENT_RE.match(value):
        report.errors.append(f"{path}: {key} must be an identifier.")


def build_flow_from_graph(
    *,
    graph: str,
    tasks: Dict[str, Task],
    pipes: Optional[Dict[str, str]] = None,
    flow_name: str = "main",
) -> Flow:
    parsed = parse_graph(graph)
    resolved = resolve_pipe_refs(parsed, pipes or {})
    fragment = _compile_pipeline(resolved, tasks)
    flow = Flow(name=flow_name)
    flow >> fragment
    return flow


def _compile_pipeline(pipeline: Pipeline, tasks: Dict[str, Task]) -> FlowFragment:
    if not pipeline.terms:
        raise GraphValidationError("Empty pipeline is not allowed.")
    fragment = _compile_term(pipeline.terms[0], tasks)
    for term in pipeline.terms[1:]:
        fragment = fragment >> _compile_term(term, tasks)
    return fragment


def _compile_term(term: Term, tasks: Dict[str, Task]) -> FlowFragment:
    if isinstance(term, TaskTerm):
        task = tasks.get(term.name)
        if task is None:
            raise GraphReferenceError(f"Task not found: {term.name}")
        return TaskWrapper(task)
    if isinstance(term, SwitchTerm):
        return _compile_switch(term, tasks)
    if isinstance(term, RepeatTerm):
        return FlowFragment(
            [
                RepeatNode(
                    body=_compile_pipeline(term.body, tasks).to_subflow(),
                    count=_compile_repeat_count(term.count),
                    collect=_compile_collect(term.collect, default="list"),
                )
            ]
        )
    if isinstance(term, ForEachTerm):
        return FlowFragment(
            [
                ForEachNode(
                    body=_compile_pipeline(term.body, tasks).to_subflow(),
                    source=ensure_expression(_compile_expression(term.over, default_to_params=True)),
                    alias=term.item,
                    index_alias=term.index,
                    collect=_compile_collect(term.collect, default="list"),
                )
            ]
        )
    if isinstance(term, UntilTerm):
        return FlowFragment(
            [
                UntilNode(
                    body=_compile_pipeline(term.body, tasks).to_subflow(),
                    condition=ensure_expression(_compile_expression(term.cond, default_to_params=False)),
                    max_iter=_compile_max_iter(term.max_iter),
                    collect=_compile_collect(term.collect, default="last"),
                )
            ]
        )
    raise GraphValidationError(f"Unsupported term type: {type(term).__name__}")


def _compile_switch(term: SwitchTerm, tasks: Dict[str, Task]) -> FlowFragment:
    cases: List[CaseNode] = []
    for case in term.cases:
        branch = _compile_pipeline(case.branch, tasks).to_subflow()
        value = _compile_case_value(case.value)
        cases.append(CaseNode(value=value, target=branch))
    if term.default is not None:
        default_branch = _compile_pipeline(term.default, tasks).to_subflow()
        cases.append(CaseNode(value=DEFAULT_CASE_VALUE, target=default_branch))
    if not cases:
        raise GraphValidationError("switch must define at least one case.")
    return FlowFragment(
        [
            SwitchNode(
                expression=ensure_expression(_compile_expression(term.on, default_to_params=True)),
                cases=cases,
            )
        ]
    )


def _compile_case_value(value: str):
    if value == "true":
        return True
    if value == "false":
        return False
    if value.isdigit():
        return int(value)
    return value


def _compile_repeat_count(raw: str):
    if raw.isdigit():
        value = int(raw)
        if value < 0:
            raise GraphValidationError("repeat count must be non-negative.")
        return value
    return ensure_expression(_compile_expression(raw, default_to_params=True))


def _compile_max_iter(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    if not raw.isdigit():
        raise GraphValidationError("until max_iter must be an integer.")
    value = int(raw)
    if value < 1:
        raise GraphValidationError("until max_iter must be >= 1.")
    return value


def _compile_collect(raw: Optional[str], *, default: str) -> str:
    mode = raw or default
    if mode not in ALLOWED_COLLECT_MODES:
        raise GraphValidationError(f"Invalid collect mode: {mode}")
    return mode


def _compile_expression(raw: str, *, default_to_params: bool) -> str:
    expr = raw.strip()
    if expr.startswith("{{") and expr.endswith("}}"):
        inner = expr[2:-2].strip()
    else:
        inner = expr

    if not inner:
        raise GraphValidationError("Expression cannot be empty.")

    if "$ctx." in inner or "$env." in inner:
        return inner

    if not PATH_RE.match(inner):
        raise GraphValidationError(
            f"Unsupported expression '{raw}'. Use simple path or explicit $ctx/$env expression."
        )

    if inner.startswith("env."):
        return f"$env.{inner[4:]}"
    if inner.startswith("ctx."):
        return f"$ctx.{inner[4:]}"

    head = inner.split(".", 1)[0]
    if head in {"params", "results", "scratch", "artifacts", "loop", "loops"}:
        return f"$ctx.{inner}"

    if "." in inner:
        return f"$ctx.{inner}"

    if default_to_params:
        return f"$ctx.params.{inner}"
    return f"$ctx.{inner}"
