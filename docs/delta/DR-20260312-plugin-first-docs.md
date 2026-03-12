# delta-request

## Delta ID
- DR-20260312-plugin-first-docs

## Delta Type
- DOCS-SYNC

## 目的
- README とチュートリアルで、Task 利用の基本導線を `flow.yaml` の `callable` 明示ではなくプラグイン登録中心へ揃える。
- `tasks.<name>.callable` は補助的な経路として位置付け直す。

## 変更対象（In Scope）
- 対象1: README / README_ja の推奨導線と例を plugin-first に更新する。
- 対象2: tutorial index / custom task tutorial の説明を plugin-first に更新する。
- 対象3: plan と delta 記録を更新する。

## 非対象（Out of Scope）
- 非対象1: loader / discovery 実装の変更。
- 非対象2: spec / architecture / concept の仕様変更。
- 非対象3: 既存 tutorial 全章の YAML サンプル全面差し替え。

## 差分仕様
- DS-01:
  - Given: ユーザーが README から Task の登録方法を学ぶ。
  - When: README / README_ja を読む。
  - Then: プラグイン登録が基本経路として示され、`callable` は補助経路として説明される。
- DS-02:
  - Given: ユーザーが tutorial で BaseTask / Task subclass の使い方を学ぶ。
  - When: custom task tutorial と index を読む。
  - Then: Task subclass は plug-in entry point で登録する流れが第一選択として説明される。

## 受入条件（Acceptance Criteria）
- AC-01: [README.md](/C:/Users/naruhide/workspace/pyoco/README.md) と [README_ja.md](/C:/Users/naruhide/workspace/pyoco/README_ja.md) が plugin-first の導線になる。
- AC-02: [07_custom_tasks.md](/C:/Users/naruhide/workspace/pyoco/docs/tutorial/07_custom_tasks.md), [07_custom_tasks_ja.md](/C:/Users/naruhide/workspace/pyoco/docs/tutorial/07_custom_tasks_ja.md), tutorial index が plugin-first の説明に更新される。
- AC-03: delta 記録と plan の整合が取れる。

## 制約
- 制約1: 実装や I/F の説明を事実以上に広げない。
- 制約2: plugin-first の主張は現行の entry point 登録経路に基づく。

## Review Gate
- required: No
- reason: 既存実装方針を README / tutorial に同期する文書差分のみ。

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-plugin-first-docs

## Delta Type
- DOCS-SYNC

## 実行ステータス
- APPLIED

## 変更ファイル
- README.md
- README_ja.md
- docs/tutorial/index.md
- docs/tutorial/index_ja.md
- docs/tutorial/07_custom_tasks.md
- docs/tutorial/07_custom_tasks_ja.md
- docs/plan.md

## 適用内容（AC対応）
- AC-01:
  - 変更: README / README_ja の Graph DSL と plug-in セクションで plug-in 登録を基本導線に明記し、`tasks.<name>.callable` を補助経路へ位置付け直した。
  - 根拠: `README.md`, `README_ja.md`
- AC-02:
  - 変更: tutorial index と custom task tutorial を、Task subclass を plug-in entry point で登録する流れを第一選択とする説明へ更新した。
  - 根拠: `docs/tutorial/index.md`, `docs/tutorial/index_ja.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`
- AC-03:
  - 変更: plan に delta 作業を記録した。
  - 根拠: `docs/plan.md`

## 非対象維持の確認
- Out of Scope への変更なし: Yes
- もし No の場合の理由:

## コード分割健全性
- 500行超のファイルあり: No
- 800行超のファイルあり: No
- 1000行超のファイルあり: No
- 長大な関数なし: Yes
- 責務過多のモジュールなし: Yes

## verify 依頼メモ
- 検証してほしい観点: plugin-first の導線が README / tutorial で一貫しているか、plan/delta 整合
- review evidence: 文書差分のみで実装変更なし

# delta-verify

## Delta ID
- DR-20260312-plugin-first-docs

## Verify Profile
- static check: 変更後の README / tutorial 文面確認
- targeted unit: 未実施（docs-only delta）
- targeted integration / E2E: 未実施（docs-only delta）
- project-validator: `validate_delta_links.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `README.md`, `README_ja.md` で plug-in が基本経路、`tasks.<name>.callable` が補助経路として明記された |
| AC-02 | PASS | tutorial index / custom task tutorial が plug-in 登録中心の説明へ更新された |
| AC-03 | PASS | `docs/plan.md` を更新し、`validate_delta_links.js` が PASS |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: 前半 tutorial の具体例には `callable` サンプルが残るが、index と README で「短い例のため」と位置付けている。

## Review Gate
- required: No
- checklist: `docs/delta/REVIEW_CHECKLIST.md`
- layer integrity: NOT CHECKED
- docs sync: PASS
- data size: NOT CHECKED
- code split health: NOT CHECKED
- file-size threshold: NOT CHECKED

## Review Delta Outcome
- pass: Yes
- follow-up delta seeds:

## 判定
- Overall: PASS

## FAIL時の最小修正指示
- なし

# delta-archive

## Delta ID
- DR-20260312-plugin-first-docs

## クローズ判定
- verify結果: PASS
- review gate: NOT REQUIRED
- archive可否: 可

## 確定内容
- 目的: README / tutorial の基本導線を plug-in 登録中心へ揃える。
- 変更対象: README / tutorial / plan
- 非対象: loader 実装、仕様書、tutorial 全章の全面差し替え

## 実装記録
- 変更ファイル: `README.md`, `README_ja.md`, `docs/tutorial/index.md`, `docs/tutorial/index_ja.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`, `docs/plan.md`
- AC達成状況: AC-01〜AC-03 PASS

## 検証記録
- verify要約: static check 完了、delta link validator PASS
- 主要な根拠: `README.md`, `README_ja.md`, `docs/tutorial/index.md`, `docs/tutorial/index_ja.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: 前半 tutorial の callable サンプルを plug-in サンプルへ全面置換する場合は、章ごとの学習コストを見ながら別 delta で分離する
