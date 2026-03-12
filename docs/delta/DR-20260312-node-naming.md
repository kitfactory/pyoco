# delta-request

## Delta ID
- DR-20260312-node-naming

## Delta Type
- FEATURE

## 目的
- flow.yaml の graph で同一 task 定義を複数回使えるよう、Task 参照と実行ノード名を分離する。
- Context 参照でノード名を使えるようにし、名前付きノードの入出力追跡を可能にする。

## 変更対象（In Scope）
- 対象1: Graph DSL に名前付き task term 構文を追加する。
- 対象2: 同一 task 定義から複数ノードを生成できるよう graph compile を拡張する。
- 対象3: Context / Engine / trace が名前付きノードを実行結果キーとして扱えるようにする。
- 対象4: spec / architecture / concept / plan / README の最小同期を行う。
- 対象5: DSL / Context / E2E テストを追加し回帰を防ぐ。

## 非対象（Out of Scope）
- 非対象1: Python API 側の `task` デコレータや `Flow >>` 構文への別名付与機能追加。
- 非対象2: server / worker / observability 系の I/F 変更。
- 非対象3: 名前付きノード以外の DSL 構文刷新や互換レイヤ追加。

## 差分仕様
- DS-01:
  - Given: graph 内で 1 つの task 定義を複数回使いたいフローがある。
  - When: ユーザーが `node_name: task_ref` 形式で task term を記述する。
  - Then: Pyoco は `task_ref` の task 定義を使って `node_name` を実行ノード名として持つノードを構築する。
- DS-02:
  - Given: 名前付きノードが実行された。
  - When: 下流 task またはユーザーが Context 参照を行う。
  - Then: `$node.<node_name>.output` と `Context.get_result(<node_name>)` で当該ノード出力を参照できる。
- DS-03:
  - Given: graph 内で同じノード名が複数回使われる、または未定義 task を参照する。
  - When: graph を build/check する。
  - Then: Pyoco は構築不能として明確なエラーを返す。

## 受入条件（Acceptance Criteria）
- AC-01: `build_flow_from_graph` が `first: shared >> second: shared` を受理し、`first` と `second` を別 Task として Flow に含める。
- AC-02: 名前付きノードの実行結果が Context / trace / run state でノード名単位に観測でき、`$node.first.output` の参照が成功する。
- AC-03: 重複ノード名または不正な名前付き構文に対するテストが追加され、graph build/check で失敗を検出できる。
- AC-04: concept / spec / architecture / plan / README が名前付きノード仕様に同期される。

## 制約
- 制約1: 既存の bare task term (`task_ref`) は後方互換で維持する。
- 制約2: 変更は名前付きノードに必要な最小差分に留め、task discovery や support 情報の仕様は変えない。

## Review Gate
- required: Yes
- reason: DSL 構文、ドメインモデル、Context 参照、文書正本が横断的に変わるため。

## Review Focus（REVIEW または review gate required の場合）
- checklist: `docs/delta/REVIEW_CHECKLIST.md`
- target area: DSL 構文の曖昧性、Task 複製時の依存関係、Context 参照キー、文書同期

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-node-naming

## Delta Type
- FEATURE

## 実行ステータス
- APPLIED

## 変更ファイル
- src/pyoco/dsl/graph.py
- src/pyoco/dsl/graph_terms.py
- src/pyoco/core/context.py
- src/pyoco/core/exceptions.py
- tests/dsl/test_graph.py
- tests/core/test_context_resolve.py
- tests/cli/test_cli.py
- tests/test_e2e_graph_dsl.py
- docs/OVERVIEW.md
- docs/concept.md
- docs/spec.md
- docs/architecture.md
- docs/plan.md
- README.md
- README_ja.md

## 適用内容（AC対応）
- AC-01:
  - 変更: Graph parser に `node_name: task_ref` を追加し、graph compile 時に同一 task 定義から別名 Task を複製できるようにした。
  - 根拠: `src/pyoco/dsl/graph.py`, `src/pyoco/dsl/graph_terms.py`, `tests/dsl/test_graph.py`
- AC-02:
  - 変更: 名前付きノードの runtime key をノード名にし、`Context.get_result` と `$node.<node>.output` の説明をノード名基準に更新した。
  - 根拠: `src/pyoco/dsl/graph.py`, `src/pyoco/core/context.py`, `src/pyoco/core/exceptions.py`, `tests/core/test_context_resolve.py`, `tests/test_e2e_graph_dsl.py`
- AC-03:
  - 変更: 重複 node_name を graph build で拒否し、CLI check でも失敗を返すテストを追加した。
  - 根拠: `src/pyoco/dsl/graph.py`, `tests/dsl/test_graph.py`, `tests/cli/test_cli.py`
- AC-04:
  - 変更: OVERVIEW/concept/spec/architecture/plan/README を名前付きノード仕様へ同期した。
  - 根拠: `docs/OVERVIEW.md`, `docs/concept.md`, `docs/spec.md`, `docs/architecture.md`, `docs/plan.md`, `README.md`, `README_ja.md`

## 非対象維持の確認
- Out of Scope への変更なし: Yes
- もし No の場合の理由:

## コード分割健全性
- 500行超のファイルあり: Yes
- 800行超のファイルあり: No
- 1000行超のファイルあり: No
- 長大な関数なし: Yes
- 責務過多のモジュールなし: Yes

## verify 依頼メモ
- 検証してほしい観点: 名前付き task 構文の build/check 実装、Context 参照キー、文書正本同期、コードサイズ閾値
- review evidence: `src/pyoco/dsl/graph.py` の AST 定義を `src/pyoco/dsl/graph_terms.py` へ分離し、split threshold を回避した

# delta-verify

## Delta ID
- DR-20260312-node-naming

## Verify Profile
- static check: 対象差分のコード読解、`git diff` 確認
- targeted unit: `uv run pytest tests/dsl tests/engine tests/core/test_context_resolve.py tests/cli/test_cli.py tests/test_e2e_graph_dsl.py`
- targeted integration / E2E: `tests/cli/test_cli.py`, `tests/test_e2e_graph_dsl.py`
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `tests/dsl/test_graph.py` で `first: shared >> second: shared` が別 Task として構築されることを確認 |
| AC-02 | PASS | `tests/core/test_context_resolve.py` と `tests/test_e2e_graph_dsl.py` で `Context.get_result("first")` と `$node.first.output` が解決されることを確認 |
| AC-03 | PASS | `tests/dsl/test_graph.py` と `tests/cli/test_cli.py` で重複 node_name が build/check 失敗になることを確認 |
| AC-04 | PASS | `docs/OVERVIEW.md`, `docs/concept.md`, `docs/spec.md`, `docs/architecture.md`, `docs/plan.md`, `README.md`, `README_ja.md` を同期済み |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: `node_name: task_ref` は bare task term より優先して parse されるため、graph 内の `:` は task naming と switch case の文脈でのみ意味を持つ。既存 `switch` / loop 回帰は対象テストで確認済み。

## Review Gate
- required: Yes
- checklist: `docs/delta/REVIEW_CHECKLIST.md`
- layer integrity: PASS
- docs sync: PASS
- data size: PASS
- code split health: PASS
- file-size threshold: PASS

## Review Delta Outcome
- pass: Yes
- follow-up delta seeds:

## 判定
- Overall: PASS

## FAIL時の最小修正指示
- なし

# delta-archive

## Delta ID
- DR-20260312-node-naming

## クローズ判定
- verify結果: PASS
- review gate: PASSED
- archive可否: 可

## 確定内容
- 目的: graph 内の task 参照と実行ノード名を分離し、同一 task 定義の複数利用とノード名参照を可能にする。
- 変更対象: Graph DSL / graph compile / Context 参照文言 / 対象テスト / 正本文書
- 非対象: Python API 別名付与、server/worker/observability、DSL 全面刷新

## 実装記録
- 変更ファイル: `src/pyoco/dsl/graph.py`, `src/pyoco/dsl/graph_terms.py`, `src/pyoco/core/context.py`, `src/pyoco/core/exceptions.py`, `tests/dsl/test_graph.py`, `tests/core/test_context_resolve.py`, `tests/cli/test_cli.py`, `tests/test_e2e_graph_dsl.py`, `docs/OVERVIEW.md`, `docs/concept.md`, `docs/spec.md`, `docs/architecture.md`, `docs/plan.md`, `README.md`, `README_ja.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: 対象 pytest 56 件 PASS、delta link validator PASS、code size validator PASS（review threshold 超えファイルは既存レビュー対象のみ）
- 主要な根拠: `tests/dsl/test_graph.py`, `tests/core/test_context_resolve.py`, `tests/cli/test_cli.py`, `tests/test_e2e_graph_dsl.py`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: Python API 側でも task 別名を付けられるようにする場合は別 delta で DSL と切り分けて検討する
