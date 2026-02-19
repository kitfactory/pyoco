from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Set


class DSLSyntaxSpikeError(ValueError):
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


class DSLLexer:
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
                raise DSLSyntaxSpikeError(
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
            raise DSLSyntaxSpikeError(f"Unexpected character '{ch}' at position {self.pos}.")
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
            raise DSLSyntaxSpikeError(f"Unterminated template expression at position {start}.")
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
        raise DSLSyntaxSpikeError(f"Unterminated string at position {start}.")

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


class DSLParserSpike:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = list(tokens)
        self.idx = 0

    def parse(self) -> Pipeline:
        pipeline = self._parse_pipeline(stop_kinds={"EOF"})
        self._expect("EOF")
        return pipeline

    def _parse_pipeline(self, stop_kinds: Set[str]) -> Pipeline:
        if self._peek().kind in stop_kinds:
            raise DSLSyntaxSpikeError(f"Empty pipeline before token '{self._peek().kind}'.")
        terms: List[Term] = [self._parse_term()]
        while self._peek().kind == "SHIFT":
            self._advance()
            terms.append(self._parse_term())
        if self._peek().kind not in stop_kinds:
            token = self._peek()
            raise DSLSyntaxSpikeError(
                f"Expected one of {sorted(stop_kinds)} but got '{token.kind}' at position {token.pos}."
            )
        return Pipeline(terms=terms)

    def _parse_term(self) -> Term:
        token = self._peek()
        if token.kind != "IDENT":
            raise DSLSyntaxSpikeError(f"Expected term at position {token.pos}, got '{token.kind}'.")
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
            raise DSLSyntaxSpikeError(f"Unknown callable term '{ident}' at position {token.pos}.")
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
            raise DSLSyntaxSpikeError("switch(...) requires 'on='.")
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
            raise DSLSyntaxSpikeError("repeat(...) requires 'count='.")
        self._expect("LBRACE")
        body = self._parse_pipeline(stop_kinds={"RBRACE"})
        self._expect("RBRACE")
        return RepeatTerm(count=count, collect=args.get("collect"), body=body)

    def _parse_foreach(self) -> ForEachTerm:
        self._expect_ident("foreach")
        args = self._parse_named_args()
        over = args.get("over")
        if not over:
            raise DSLSyntaxSpikeError("foreach(...) requires 'over='.")
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
            raise DSLSyntaxSpikeError("until(...) requires 'cond='.")
        self._expect("LBRACE")
        body = self._parse_pipeline(stop_kinds={"RBRACE"})
        self._expect("RBRACE")
        return UntilTerm(
            cond=cond,
            max_iter=args.get("max_iter"),
            collect=args.get("collect"),
            body=body,
        )

    def _parse_named_args(self) -> dict[str, str]:
        args: dict[str, str] = {}
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
            return parse_pipeline_spike(quoted)
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
            raise DSLSyntaxSpikeError(
                f"Expected '{kind}' at position {token.pos}, got '{token.kind}'."
            )
        self.idx += 1
        return token

    def _expect_ident(self, value: str):
        token = self._expect("IDENT")
        if token.value != value:
            raise DSLSyntaxSpikeError(
                f"Expected '{value}' at position {token.pos}, got '{token.value}'."
            )

    def _expect_any(self, kinds: Iterable[str]) -> Token:
        allowed = set(kinds)
        token = self._peek()
        if token.kind not in allowed:
            raise DSLSyntaxSpikeError(
                f"Expected one of {sorted(allowed)} at position {token.pos}, got '{token.kind}'."
            )
        self.idx += 1
        return token


def tokenize_spike(text: str) -> List[Token]:
    return DSLLexer(text).tokenize()


def parse_pipeline_spike(text: str) -> Pipeline:
    return DSLParserSpike(tokenize_spike(text)).parse()

