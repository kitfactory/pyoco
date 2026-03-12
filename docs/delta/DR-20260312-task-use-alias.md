# delta-request

## Delta ID
- DR-20260312-task-use-alias

## Delta Type
- FEATURE

## 目的
- `flow.yaml` の `tasks.<name>` で、plug-in が公開した task 名を `use` で参照できるようにする。
- README / tutorial / plug-in guide を `use` 正規ルートへ同期し、公開名の推奨命名を `namespace/task_name` に揃える。

## 変更対象（In Scope）
- 対象1: `TaskConfig` に `use` を追加し、`callable` と併用不可の設定検証を入れる。
- 対象2: `TaskLoader` に `use` 解決を追加し、登録済み task をローカル名へ束ねられるようにする。
- 対象3: `schemas/discovery/support` の対象テストを追加・更新する。
- 対象4: OVERVIEW / concept / spec / architecture / plan / README / tutorial / plugins guide を `use` 中心の説明へ更新する。

## 非対象（Out of Scope）
- 非対象1: graph DSL の構文変更。
- 非対象2: plug-in registry の API 変更。
- 非対象3: `callable` の削除。

## 差分仕様
- DS-01:
  - Given: plug-in が公開した task 名がある。
  - When: ユーザーが `tasks.classify.use: "vision/image_classify"` のように定義する。
  - Then: Pyoco は公開 task を `classify` というローカル task 名で利用できる。
- DS-02:
  - Given: 同じ公開 task 名を複数のローカル名で使いたい。
  - When: `tasks.classify.use` と `tasks.classify2.use` が同じ公開名を参照する。
  - Then: graph では `classify >> classify2` のように別 task 名として扱える。
- DS-03:
  - Given: `use` が未登録 task を参照する、または `use` と `callable` を同時指定する。
  - When: config/load を行う。
  - Then: Pyoco は設定エラーとして明確に失敗する。

## 受入条件（Acceptance Criteria）
- AC-01: `tasks.<local>.use: "<public_name>"` を読み込み、公開 task をローカル名へ束ねるテストが追加される。
- AC-02: 同一公開 task を複数ローカル名へ束ねて `graph: classify >> classify2` のように使える。
- AC-03: `use` 不正参照と `use`/`callable` 併用の失敗がテストで担保される。
- AC-04: README / tutorial / plugins guide / support guide / 正本文書が `use` を正規ルートとして説明する。

## 制約
- 制約1: `callable` は互換用途として残す。
- 制約2: 公開名の推奨表記は `namespace/task_name` とし、`.` より `/` を優先して説明する。

## Review Gate
- required: Yes
- reason: config I/F、loader、文書正本、guide 出力が横断的に変わるため。

## Review Focus（REVIEW または review gate required の場合）
- checklist: `docs/delta/REVIEW_CHECKLIST.md`
- target area: `use` 解決順、overlay 挙動、`callable` 互換、公開名命名方針、文書同期

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-task-use-alias

## Delta Type
- FEATURE

## 実行ステータス
- APPLIED

## 変更ファイル
- src/pyoco/schemas/config.py
- src/pyoco/discovery/loader.py
- src/pyoco/support/renderer.py
- src/pyoco/core/base_task.py
- tests/schemas/test_config.py
- tests/discovery/test_loader.py
- tests/support/test_support_info.py
- README.md
- README_ja.md
- docs/plugins.md
- docs/tutorial/index.md
- docs/tutorial/index_ja.md
- docs/tutorial/01_hello.md
- docs/tutorial/01_hello_ja.md
- docs/tutorial/07_custom_tasks.md
- docs/tutorial/07_custom_tasks_ja.md
- docs/OVERVIEW.md
- docs/concept.md
- docs/spec.md
- docs/architecture.md
- docs/plan.md

## 適用内容（AC対応）
- AC-01:
  - 変更: `TaskConfig.use` と設定検証を追加し、`TaskLoader` で登録済み公開 task 名をローカル task 名へ束ねる alias 解決を実装した。
  - 根拠: `src/pyoco/schemas/config.py`, `src/pyoco/discovery/loader.py`, `tests/schemas/test_config.py`, `tests/discovery/test_loader.py`
- AC-02:
  - 変更: 同一公開 task を複数ローカル名へ束ね、`graph: classify >> classify2` のように使える loader/build 経路を追加した。
  - 根拠: `src/pyoco/discovery/loader.py`, `tests/discovery/test_loader.py`
- AC-03:
  - 変更: `use` 不正参照と `use`/`callable` 併用の失敗を設定テストで担保した。
  - 根拠: `tests/schemas/test_config.py`, `tests/discovery/test_loader.py`
- AC-04:
  - 変更: README / tutorial / plugins guide / support guide / 正本文書を `use` 正規ルート + `namespace/task_name` 推奨へ更新した。
  - 根拠: `README.md`, `README_ja.md`, `docs/plugins.md`, `docs/tutorial/*.md`, `docs/spec.md`, `docs/architecture.md`, `docs/concept.md`, `src/pyoco/support/renderer.py`

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
- 検証してほしい観点: `use` 解決順、`callable` 互換、guide 出力、公開名命名方針
- review evidence: code size validator では `graph.py` / `engine.py` / `cli/main.py` が review threshold 超えだが split threshold 超えはなし

# delta-verify

## Delta ID
- DR-20260312-task-use-alias

## Verify Profile
- static check: 変更差分と docs 文言確認
- targeted unit: `uv run pytest tests/schemas/test_config.py tests/discovery/test_loader.py tests/support/test_support_info.py tests/dsl/test_graph.py tests/core/test_context_resolve.py tests/cli/test_cli.py tests/test_e2e_graph_dsl.py`
- targeted integration / E2E: `uv run pytest tests/plugins tests/support/test_support_info.py tests/discovery/test_loader.py tests/schemas/test_config.py`
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `tests/schemas/test_config.py` と `tests/discovery/test_loader.py` で `use` の設定読込と alias 解決を確認 |
| AC-02 | PASS | `tests/discovery/test_loader.py` で同一公開 task を `classify` / `classify2` として graph build できることを確認 |
| AC-03 | PASS | `tests/schemas/test_config.py` と `tests/discovery/test_loader.py` で `use`/`callable` 併用と未登録参照の失敗を確認 |
| AC-04 | PASS | README / tutorial / plugins guide / support guide / 正本文書を `use` 中心へ同期し、`tests/support/test_support_info.py` で guide 出力を確認 |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: 旧 tutorial の一部章では簡潔さのため `callable` 例が残るが、README / index / custom task tutorial で `use` 正規ルートを明示した。

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
- DR-20260312-task-use-alias

## クローズ判定
- verify結果: PASS
- review gate: PASSED
- archive可否: 可

## 確定内容
- 目的: plug-in 公開名を `tasks.<local>.use` で束ねる正規ルートを追加し、docs/guide をその導線へ揃える。
- 変更対象: config / loader / support guide / tests / README / tutorial / 正本文書
- 非対象: graph DSL 構文変更、plug-in registry API 変更、`callable` 削除

## 実装記録
- 変更ファイル: `src/pyoco/schemas/config.py`, `src/pyoco/discovery/loader.py`, `src/pyoco/support/renderer.py`, `src/pyoco/core/base_task.py`, `tests/schemas/test_config.py`, `tests/discovery/test_loader.py`, `tests/support/test_support_info.py`, `README.md`, `README_ja.md`, `docs/plugins.md`, `docs/tutorial/*.md`, `docs/OVERVIEW.md`, `docs/concept.md`, `docs/spec.md`, `docs/architecture.md`, `docs/plan.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: 対象 pytest 45件 + 23件 PASS、delta link validator PASS、code size validator PASS
- 主要な根拠: `tests/schemas/test_config.py`, `tests/discovery/test_loader.py`, `tests/support/test_support_info.py`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: tutorial 前半章の `callable` 例を `use` 中心へ全面置換する場合は、学習導線を崩さない単位で別 delta に分割する
