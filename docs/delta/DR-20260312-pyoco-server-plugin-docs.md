# delta-request

## Delta ID
- DR-20260312-pyoco-server-plugin-docs

## Delta Type
- DOCS-SYNC

## 目的
- plug-in 形式にする価値として、`pyoco-server` での配布・同期のしやすさを docs に明示する。
- `pyoco-server` が担う分散実行と wheel 配布の文脈を、README / plug-in guide / custom task tutorial で自然に伝える。

## 変更対象（In Scope）
- 対象1: `README.md` / `README_ja.md` の `pyoco-server` / plug-in 説明に、plug-in 配布の価値を追記する。
- 対象2: `docs/plugins.md` に、`pyoco-server` で plug-in wheel を配布しやすい理由を追記する。
- 対象3: `docs/tutorial/07_custom_tasks*.md` に、plug-in 化が `pyoco-server` 配布と相性が良いことを追記する。
- 対象4: `docs/OVERVIEW.md` / `docs/plan.md` と delta 記録に今回の docs sync を反映する。

## 非対象（Out of Scope）
- 非対象1: `pyoco-server` 側のコード・設定手順の詳細説明。
- 非対象2: pyoco 本体の worker/server 実装変更。
- 非対象3: `pyoco-server` との互換 API 追加。

## 差分仕様
- DS-01:
  - Given: 現在の docs では「plug-in を選ぶ理由」と「pyoco-server での配布」のつながりが薄い。
  - When: docs を更新する。
  - Then: 読者は、plug-in 化すると `pyoco-server` の worker 群へ wheel として配布しやすいと理解できる。
- DS-02:
  - Given: `pyoco-server` は本 repo 外の別プロダクトである。
  - When: docs を更新する。
  - Then: pyoco 側 docs は概要だけを述べ、詳細は `pyoco-server` の公式 docs へ誘導する。

## 受入条件（Acceptance Criteria）
- AC-01: README / README_ja に、plug-in 形式が `pyoco-server` 配布と相性が良い旨が追記される。
- AC-02: `docs/plugins.md` と `docs/tutorial/07_custom_tasks*.md` に、`pyoco-server` 配布文脈が追記される。
- AC-03: 追記内容は `pyoco-server` の公式情報と矛盾せず、詳細手順は `pyoco-server` 側へ誘導する。
- AC-04: `docs/OVERVIEW.md` / `docs/plan.md` / delta 記録に今回の差分が残る。

## 制約
- 制約1: docs-only で閉じる。
- 制約2: `pyoco-server` の詳細仕様は要約に留め、誤って本 repo の責務に見えない書き方にする。

## Review Gate
- required: No
- reason: 他リポジトリ連携の説明追加だが、pyoco 本体の I/F や仕様変更は含まないため。

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-pyoco-server-plugin-docs

## Delta Type
- DOCS-SYNC

## 実行ステータス
- APPLIED

## 変更ファイル
- README.md
- README_ja.md
- docs/plugins.md
- docs/tutorial/07_custom_tasks.md
- docs/tutorial/07_custom_tasks_ja.md
- docs/OVERVIEW.md
- docs/plan.md
- docs/delta/DR-20260312-pyoco-server-plugin-docs.md

## 適用内容（AC対応）
- AC-01:
  - 変更: README / README_ja の `pyoco-server` / plug-in 説明に、plug-in package が worker 配布と相性が良い旨を追記した。
  - 根拠: `README.md`, `README_ja.md`
- AC-02:
  - 変更: `docs/plugins.md` と `docs/tutorial/07_custom_tasks*.md` に、plug-in wheel 配布と `pyoco-server` worker 連携の価値を追記した。
  - 根拠: `docs/plugins.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`
- AC-03:
  - 変更: 詳細手順は `pyoco-server` 側 docs を参照する形に留め、pyoco 側 docs では概要だけを説明した。
  - 根拠: `README.md`, `README_ja.md`, `docs/plugins.md`
- AC-04:
  - 変更: `docs/OVERVIEW.md` / `docs/plan.md` / delta 記録へ今回の docs sync を反映した。
  - 根拠: `docs/OVERVIEW.md`, `docs/plan.md`, `docs/delta/DR-20260312-pyoco-server-plugin-docs.md`

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
- 検証してほしい観点: `pyoco-server` との責務分離、plug-in 配布価値の明確さ、外部情報との整合、delta-plan 整合
- review evidence: `pyoco-server` 公式情報確認 + docs-only validator を実施する

# delta-verify

## Delta ID
- DR-20260312-pyoco-server-plugin-docs

## Verify Profile
- static check: README / guide / tutorial 差分を確認し、plug-in package と `pyoco-server` 配布価値の説明が入っていることを確認
- targeted unit: 実施なし（docs-only）
- targeted integration / E2E: 実施なし（docs-only）
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `README.md` / `README_ja.md` に plug-in package と worker 配布の価値を追記 |
| AC-02 | PASS | `docs/plugins.md` / `docs/tutorial/07_custom_tasks*.md` に `pyoco-server` 配布文脈を追記 |
| AC-03 | PASS | 詳細は `pyoco-server` 側 docs 参照に留め、pyoco 側 docs の責務を超えていない |
| AC-04 | PASS | `docs/OVERVIEW.md` / `docs/plan.md` / delta 記録へ反映 |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: `pyoco-server` 側の詳細機能は今後変わりうるため、pyoco 側 docs では概要説明と公式リンクに留めた。

## Review Gate
- required: No
- checklist: `docs/delta/REVIEW_CHECKLIST.md`
- layer integrity: NOT CHECKED
- docs sync: PASS
- data size: NOT CHECKED
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
- DR-20260312-pyoco-server-plugin-docs

## クローズ判定
- verify結果: PASS
- review gate: NOT REQUIRED
- archive可否: 可

## 確定内容
- 目的: plug-in 形式が `pyoco-server` 配布と相性が良いことを docs で明示する。
- 変更対象: `README.md`, `README_ja.md`, `docs/plugins.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`, `docs/OVERVIEW.md`, `docs/plan.md`
- 非対象: `pyoco-server` 詳細手順、本体実装変更、互換 API 追加

## 実装記録
- 変更ファイル: `README.md`, `README_ja.md`, `docs/plugins.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`, `docs/OVERVIEW.md`, `docs/plan.md`, `docs/delta/DR-20260312-pyoco-server-plugin-docs.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: `pyoco-server` 公式情報確認のうえ docs 差分を確認し、`validate_delta_links.js` PASS、`check_code_size.js` PASS（既存 WARN 3件）を確認
- 主要な根拠: `README.md`, `README_ja.md`, `docs/plugins.md`, `docs/tutorial/07_custom_tasks*.md`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: `pyoco-server` 側で plug-in wheel 配布の具体例が安定したら、pyoco 側 docs に最小のリンク付き例を追加する
