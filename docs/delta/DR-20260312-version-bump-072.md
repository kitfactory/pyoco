# delta-request

## Delta ID
- DR-20260312-version-bump-072

## Delta Type
- OPS

## 目的
- パッケージ版番号を `0.7.1` から `0.7.2` へ更新する。
- lockfile と版番号露出ドキュメントの表記を同期する。

## 変更対象（In Scope）
- 対象1: `pyproject.toml` の project version を `0.7.2` へ更新する。
- 対象2: `uv.lock` 内のローカル package version を `0.7.2` へ同期する。
- 対象3: 明示的に `0.7.1` を表示しているドキュメント表記を `0.7.2` へ更新する。
- 対象4: `docs/plan.md` と delta 記録に今回の version bump を反映する。

## 非対象（Out of Scope）
- 非対象1: 依存関係の追加・削除・更新。
- 非対象2: API / DSL / 実行仕様の変更。
- 非対象3: changelog 新設やリリースノートの大幅整理。

## 差分仕様
- DS-01:
  - Given: 現在の package version が `0.7.1` である。
  - When: 今回の差分を適用する。
  - Then: パッケージ定義上の version は `0.7.2` になる。
- DS-02:
  - Given: lockfile と docs に `0.7.1` の露出箇所がある。
  - When: 今回の差分を適用する。
  - Then: 対象箇所は `0.7.2` に同期され、版番号の不整合が残らない。

## 受入条件（Acceptance Criteria）
- AC-01: `pyproject.toml` の package version が `0.7.2` に更新される。
- AC-02: `uv.lock` のローカル `pyoco` package version が `0.7.2` に更新される。
- AC-03: 版番号を明示する docs 表記が `0.7.2` に更新される。
- AC-04: `docs/plan.md` と `docs/delta/DR-20260312-version-bump-072.md` に今回の差分記録が残る。

## 制約
- 制約1: 変更は版番号同期に限定し、依存解決や機能変更を混ぜない。
- 制約2: 既存の未コミット変更は巻き戻さない。

## Review Gate
- required: No
- reason: 版番号同期のみの運用差分であり、I/F や仕様変更を含まないため。

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-version-bump-072

## Delta Type
- OPS

## 実行ステータス
- APPLIED

## 変更ファイル
- pyproject.toml
- uv.lock
- docs/plugins.md
- docs/plan.md
- docs/delta/DR-20260312-version-bump-072.md

## 適用内容（AC対応）
- AC-01:
  - 変更: `pyproject.toml` の project version を `0.7.2` へ更新した。
  - 根拠: `pyproject.toml`
- AC-02:
  - 変更: `uv.lock` のローカル `pyoco` package version を `0.7.2` へ同期した。
  - 根拠: `uv.lock`
- AC-03:
  - 変更: 明示 version を含む plug-in guide 見出しを `v0.7.2` へ更新した。
  - 根拠: `docs/plugins.md`
- AC-04:
  - 変更: version bump の delta 記録を追加し、`docs/plan.md` の current/archive に反映した。
  - 根拠: `docs/delta/DR-20260312-version-bump-072.md`, `docs/plan.md`

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
- 検証してほしい観点: package version / lockfile / docs 表記 / delta-plan 整合
- review evidence: `uv lock --check` と `project-validator` を実施する

# delta-verify

## Delta ID
- DR-20260312-version-bump-072

## Verify Profile
- static check: `rg -n --fixed-strings "0.7.1" . -g "!docs/delta/DR-20260312-version-bump-072.md"` で旧版番号残存がないことを確認
- targeted unit: 実施なし（版番号同期のみ）
- targeted integration / E2E: `uv lock --check`
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `pyproject.toml` の project version が `0.7.2` |
| AC-02 | PASS | `uv.lock` の editable package `pyoco` version が `0.7.2` |
| AC-03 | PASS | 明示版番号の docs 表記が `docs/plugins.md` の `v0.7.2` に同期 |
| AC-04 | PASS | delta 記録と `docs/plan.md` に version bump の履歴を追加 |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: `check_code_size.js` では既存の `graph.py` / `engine.py` / `cli/main.py` が review threshold 超えの WARN を継続しているが、今回差分では新規の長大化はない。

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
- DR-20260312-version-bump-072

## クローズ判定
- verify結果: PASS
- review gate: NOT REQUIRED
- archive可否: 可

## 確定内容
- 目的: package / lockfile / docs の版番号を `0.7.2` へ同期する。
- 変更対象: `pyproject.toml`, `uv.lock`, `docs/plugins.md`, `docs/plan.md`
- 非対象: 依存関係更新、API/DSL/実行仕様変更、changelog 再編

## 実装記録
- 変更ファイル: `pyproject.toml`, `uv.lock`, `docs/plugins.md`, `docs/plan.md`, `docs/delta/DR-20260312-version-bump-072.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: 旧版番号検索（current delta 自身を除外）で残存なし、`uv lock --check` PASS、`validate_delta_links.js` PASS、`check_code_size.js` PASS（WARN 3件）を確認
- 主要な根拠: `pyproject.toml`, `uv.lock`, `docs/plugins.md`, `docs/plan.md`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- なし
