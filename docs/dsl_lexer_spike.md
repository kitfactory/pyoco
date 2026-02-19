# DSL字句解析スパイク（`>>` 固定）

## 目的
- block構文（`{ ... }`）と YAML 複数行入力を前提に、`switch` / `repeat` / `foreach` / `until` / `pipe(NAME)` を字句解析・構文解析できるかを先行検証する。

## 実装範囲
- スパイク実装: `src/pyoco/dsl/spike_parser.py`
- スパイクテスト: `tests/dsl/test_spike_parser.py`
- 本体CLI/Engineには未接続（非侵襲）。

## 採用文法（スパイクで成立）
- 連結演算子: `>>` のみ。単独 `>` はエラー。
- Term:
  - `TaskName`
  - `pipe(NAME)`
  - `switch(on=...){ ... }`
  - `repeat(count=..., collect=...){ ... }`
  - `foreach(over=..., item=..., index=..., collect=...){ ... }`
  - `until(cond=..., max_iter=..., collect=...){ ... }`
- `switch` branch:
  - `case: inline pipeline;`
  - `case: "quoted >> pipeline";`
  - `default: ...;`
- `{{ ... }}` テンプレ表現を1トークンとして扱う。
- `#` 行コメントを字句段階で無視する。

## 不採用・保留（この段階では対応しない）
- `loop(...)`（要件で不採用）。
- 互換レイヤ（旧記法の受理）。
- 式の実評価（dry-run 形式検証のみ）。
- 文字列内での高度なエスケープ仕様の厳密化。

## 失敗パターン（検出できたもの）
- `A > B` のような単独 `>`。
- `{{` で始まり `}}` が閉じないテンプレ。
- 未知のcallable term（例: `unknown(...)`）。
- 区切り不足（`;`, `}`, `)` など）。

## テスト結果
- 実行: `.venv/bin/pytest tests/dsl/test_spike_parser.py`
- 結果: 5 passed

## 実装移行時の注意
- スパイクは AST/エラー体系を簡略化しているため、本実装では `ERR-PYOCO-0014..0018` と整合する例外型へ置き換える。
- `pipe` 展開上限（深さ128 / Term数4096）は Resolver 層で厳密化する。
- `switch default` 省略時エラー、`collect` 既定値（repeat/foreach=list, until=last）を Engine 層で強制する。
