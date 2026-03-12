# delta-request

## Delta ID
- DR-20260312-doc-onboarding-refresh

## Delta Type
- DOCS-SYNC

## 目的
- README / tutorial の入口文書を、現在の推奨モデルに沿った説明へ寄せつつ、楽しく試しやすい導線へ改善する。
- 古い学習モデルに見える表現を減らし、`use` / plug-in 登録が正規ルートであることを読みやすく伝える。

## 変更対象（In Scope）
- 対象1: `README.md` / `README_ja.md` の冒頭導線、クイックスタート、推奨モデル説明を読みやすく更新する。
- 対象2: `docs/tutorial/index*.md` の導入と章ガイドを、試しやすさと学習順が伝わる形へ更新する。
- 対象3: `docs/tutorial/01_hello*.md` / `docs/tutorial/07_custom_tasks*.md` を、現行推奨モデルとの関係が誤解されない表現へ更新する。
- 対象4: `docs/plan.md` と delta 記録に今回の docs refresh を反映する。

## 非対象（Out of Scope）
- 非対象1: 実装コード、CLI、DSL、loader の挙動変更。
- 非対象2: tutorial 全章の全面改稿。
- 非対象3: 新しいチュートリアル章の追加。

## 差分仕様
- DS-01:
  - Given: README の冒頭が旧来の学習モデルに寄って見える。
  - When: 導線を更新する。
  - Then: 「すぐ試せる最短ルート」と「再利用向けの推奨ルート」が区別され、読者が次の一歩を選びやすくなる。
- DS-02:
  - Given: tutorial index / hello / custom tasks に硬い説明が残っている。
  - When: 文体と章導線を更新する。
  - Then: 章の目的、読む順番、`callable` が簡易例であること、plug-in + `use` が正規ルートであることが短く伝わる。
- DS-03:
  - Given: user は楽しい・簡単・試したい印象を求めている。
  - When: 見出しや導入に絵文字や短い誘導文を追加する。
  - Then: 技術的な正確性を保ったまま、入口文書の心理的なハードルが下がる。

## 受入条件（Acceptance Criteria）
- AC-01: README / README_ja が、最短導線と推奨導線を区別して案内する。
- AC-02: tutorial index / hello / custom tasks で、現行推奨モデルとの関係が明示され、古いモデルの誤読を減らす。
- AC-03: 入口文書に fun / easy を感じる表現改善が入り、絵文字や短い誘導文が追加される。
- AC-04: `docs/plan.md` と `docs/delta/DR-20260312-doc-onboarding-refresh.md` に差分記録が残る。

## 制約
- 制約1: 仕様やコマンド例の意味は変えず、docs-only で閉じる。
- 制約2: `callable` は簡易例として残せるが、正規ルートに見えない書き方にする。

## Review Gate
- required: No
- reason: README / tutorial の表現改善が中心で、I/F や仕様変更を含まないため。

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-doc-onboarding-refresh

## Delta Type
- DOCS-SYNC

## 実行ステータス
- APPLIED

## 変更ファイル
- README.md
- README_ja.md
- docs/tutorial/index.md
- docs/tutorial/index_ja.md
- docs/tutorial/01_hello.md
- docs/tutorial/01_hello_ja.md
- docs/tutorial/07_custom_tasks.md
- docs/tutorial/07_custom_tasks_ja.md
- docs/OVERVIEW.md
- docs/plan.md
- docs/delta/DR-20260312-doc-onboarding-refresh.md

## 適用内容（AC対応）
- AC-01:
  - 変更: README / README_ja の冒頭を「最短で試す入口」と「推奨ルート」に分け、plug-in + `use` を継続利用の標準導線として前方に出した。
  - 根拠: `README.md`, `README_ja.md`
- AC-02:
  - 変更: tutorial index / hello / custom tasks で、簡易 `callable` 例と推奨 plug-in ルートの関係を短く明示した。
  - 根拠: `docs/tutorial/index*.md`, `docs/tutorial/01_hello*.md`, `docs/tutorial/07_custom_tasks*.md`
- AC-03:
  - 変更: 見出し・導入文・章ガイドに絵文字と短い誘導文を入れ、試しやすさを強めた。
  - 根拠: `README.md`, `README_ja.md`, `docs/tutorial/*.md`
- AC-04:
  - 変更: `docs/OVERVIEW.md` / `docs/plan.md` / delta 記録に今回の docs refresh を反映した。
  - 根拠: `docs/OVERVIEW.md`, `docs/plan.md`, `docs/delta/DR-20260312-doc-onboarding-refresh.md`

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
- 検証してほしい観点: plugin-first 導線、`callable` の位置づけ、README / tutorial の入口導線、delta-plan 整合
- review evidence: docs-only のため validator と差分確認を中心に実施する

# delta-verify

## Delta ID
- DR-20260312-doc-onboarding-refresh

## Verify Profile
- static check: README / tutorial の変更差分を確認し、`callable` が簡易例、plug-in + `use` が推奨ルートとして読めることを確認
- targeted unit: 実施なし（docs-only）
- targeted integration / E2E: 実施なし（docs-only）
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | `README.md` / `README_ja.md` に最短導線と推奨導線を分けた導入を追加 |
| AC-02 | PASS | `docs/tutorial/index*.md` / `01_hello*.md` / `07_custom_tasks*.md` で推奨モデルとの関係を明示 |
| AC-03 | PASS | 見出しと導入に絵文字・短い誘導文を追加し、入口文書のトーンを改善 |
| AC-04 | PASS | `docs/OVERVIEW.md` / `docs/plan.md` / delta 記録を同期 |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: docs-only 変更のため実装回帰はないが、今後 tutorial の後半章にも同じトーンを広げる場合は別 delta で揃えるのがよい。

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
- DR-20260312-doc-onboarding-refresh

## クローズ判定
- verify結果: PASS
- review gate: NOT REQUIRED
- archive可否: 可

## 確定内容
- 目的: README / tutorial の入口文書を、現行推奨モデルと fun / easy な導線が両立する形へ更新する。
- 変更対象: `README.md`, `README_ja.md`, `docs/tutorial/index*.md`, `docs/tutorial/01_hello*.md`, `docs/tutorial/07_custom_tasks*.md`, `docs/OVERVIEW.md`, `docs/plan.md`
- 非対象: 実装変更、tutorial 全章改稿、新章追加

## 実装記録
- 変更ファイル: `README.md`, `README_ja.md`, `docs/tutorial/index.md`, `docs/tutorial/index_ja.md`, `docs/tutorial/01_hello.md`, `docs/tutorial/01_hello_ja.md`, `docs/tutorial/07_custom_tasks.md`, `docs/tutorial/07_custom_tasks_ja.md`, `docs/OVERVIEW.md`, `docs/plan.md`, `docs/delta/DR-20260312-doc-onboarding-refresh.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: docs 差分確認で導線改善を確認し、`validate_delta_links.js` PASS、`check_code_size.js` PASS（既存 WARN 3件）を確認
- 主要な根拠: `README.md`, `README_ja.md`, `docs/tutorial/index*.md`, `docs/tutorial/01_hello*.md`, `docs/tutorial/07_custom_tasks*.md`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: tutorial 02〜08 章の本文トーンと導線も今回の入口刷新に合わせて揃える場合は、章単位で別 delta に分ける
