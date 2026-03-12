# delta-request

## Delta ID
- DR-20260312-tutorial-tone-refresh

## Delta Type
- DOCS-SYNC

## 目的
- tutorial 02〜08 章の本文トーンを入口文書に合わせ、楽しく試しやすい導線へ揃える。
- 簡易 `callable` 例と、継続利用向けの plug-in + `use` 推奨モデルの関係を各章で誤読しにくくする。

## 変更対象（In Scope）
- 対象1: `docs/tutorial/02_params*.md` / `03_data_flow*.md` / `04_parallel*.md` / `05_artifacts*.md` / `06_errors*.md` / `08_control*.md` の導入・見出し・案内文を更新する。
- 対象2: 古い時制や旧モデルに見える表現を、現行の推奨モデルに沿う説明へ置き換える。
- 対象3: `docs/plan.md` と delta 記録に今回の tutorial refresh を反映する。

## 非対象（Out of Scope）
- 非対象1: 実装コード、CLI、DSL、loader の挙動変更。
- 非対象2: 新しい tutorial 章の追加。
- 非対象3: README の再改稿。

## 差分仕様
- DS-01:
  - Given: tutorial 02〜08 に硬い導入や旧モデルに見える表現が残っている。
  - When: 導入文と案内文を更新する。
  - Then: 各章で「何を得る章か」「次にどう進むか」が短く伝わる。
- DS-02:
  - Given: 一部の章では `callable` 例や古い時制表現がそのまま残っている。
  - When: 現行の docs 方針に沿って更新する。
  - Then: `callable` は簡易例、plug-in + `use` は継続利用の推奨ルートとして読める。
- DS-03:
  - Given: user は fun / easy / 試したくなる導線を求めている。
  - When: 見出し、短い誘導文、章のゴール説明を追加する。
  - Then: tutorial 後半章も入口文書と同じ体験で読める。

## 受入条件（Acceptance Criteria）
- AC-01: tutorial 02〜08 章に、章の目的や読む意義が分かる導入が追加される。
- AC-02: `callable` と plug-in + `use` の位置づけが、少なくとも relevant な章で明示される。
- AC-03: 古い時制や古い機能紹介に見える表現が整理され、現行 docs と矛盾しない。
- AC-04: `docs/plan.md` と `docs/delta/DR-20260312-tutorial-tone-refresh.md` に差分記録が残る。

## 制約
- 制約1: docs-only で閉じ、コマンドや仕様の意味は変えない。
- 制約2: tutorial の例コードは最小修正に留め、学習の主旨を崩さない。

## Review Gate
- required: No
- reason: tutorial 文面の同期と導線改善が中心で、I/F や仕様変更を含まないため。

## 未確定事項
- なし

# delta-apply

## Delta ID
- DR-20260312-tutorial-tone-refresh

## Delta Type
- DOCS-SYNC

## 実行ステータス
- APPLIED

## 変更ファイル
- docs/tutorial/02_params.md
- docs/tutorial/02_params_ja.md
- docs/tutorial/03_data_flow.md
- docs/tutorial/03_data_flow_ja.md
- docs/tutorial/04_parallel.md
- docs/tutorial/04_parallel_ja.md
- docs/tutorial/05_artifacts.md
- docs/tutorial/05_artifacts_ja.md
- docs/tutorial/06_errors.md
- docs/tutorial/06_errors_ja.md
- docs/tutorial/08_control.md
- docs/tutorial/08_control_ja.md
- docs/plan.md
- docs/delta/DR-20260312-tutorial-tone-refresh.md

## 適用内容（AC対応）
- AC-01:
  - 変更: tutorial 02〜08 の各章に、章の価値や目的が伝わる導入文と見出しトーンを追加した。
  - 根拠: `docs/tutorial/02*.md`, `docs/tutorial/03*.md`, `docs/tutorial/04*.md`, `docs/tutorial/05*.md`, `docs/tutorial/06*.md`, `docs/tutorial/08*.md`
- AC-02:
  - 変更: `callable` は小さな例のための簡易導線であり、継続利用は plug-in + `use` が推奨であることを relevant な章へ追記した。
  - 根拠: `docs/tutorial/02*.md`, `docs/tutorial/03*.md`, `docs/tutorial/04*.md`, `docs/tutorial/08*.md`
- AC-03:
  - 変更: 古い時制表現（例: `v0.2.0` 起点の紹介）を外し、現行 docs と矛盾しない説明へ更新した。
  - 根拠: `docs/tutorial/08_control.md`, `docs/tutorial/08_control_ja.md`
- AC-04:
  - 変更: `docs/plan.md` と delta 記録へ今回の tutorial refresh を反映した。
  - 根拠: `docs/plan.md`, `docs/delta/DR-20260312-tutorial-tone-refresh.md`

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
- 検証してほしい観点: tutorial 導線の一貫性、`callable` と `use` の位置づけ、古い表現の整理、delta-plan 整合
- review evidence: docs-only のため validator と差分確認を中心に実施する

# delta-verify

## Delta ID
- DR-20260312-tutorial-tone-refresh

## Verify Profile
- static check: tutorial 02〜08 の差分を確認し、導入文・current-model 位置づけ・古い表現の整理を確認
- targeted unit: 実施なし（docs-only）
- targeted integration / E2E: 実施なし（docs-only）
- project-validator: `validate_delta_links.js`, `check_code_size.js`

## 検証結果（AC単位）
| AC | 結果(PASS/FAIL) | 根拠 |
|---|---|---|
| AC-01 | PASS | tutorial 02〜08 で導入文と見出しトーンを更新 |
| AC-02 | PASS | relevant 章で `callable` は簡易例、plug-in + `use` が推奨ルートと明示 |
| AC-03 | PASS | 08章の `v0.2.0` 起点の説明を除去し、現行 docs に合わせた |
| AC-04 | PASS | `docs/plan.md` と delta 記録へ反映 |

## スコープ逸脱チェック
- Out of Scope 変更の有無: No
- 逸脱内容:

## 不整合/回帰リスク
- R-01: docs-only 変更のため実装回帰はないが、今後 examples 自体を plug-in-first に寄せる場合は別 delta で example コードも合わせるとより一貫する。

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
- DR-20260312-tutorial-tone-refresh

## クローズ判定
- verify結果: PASS
- review gate: NOT REQUIRED
- archive可否: 可

## 確定内容
- 目的: tutorial 02〜08 の本文トーンと current-model 導線を入口文書に合わせて揃える。
- 変更対象: `docs/tutorial/02*.md`, `docs/tutorial/03*.md`, `docs/tutorial/04*.md`, `docs/tutorial/05*.md`, `docs/tutorial/06*.md`, `docs/tutorial/08*.md`, `docs/plan.md`
- 非対象: 実装変更、新章追加、README 再改稿

## 実装記録
- 変更ファイル: `docs/tutorial/02_params.md`, `docs/tutorial/02_params_ja.md`, `docs/tutorial/03_data_flow.md`, `docs/tutorial/03_data_flow_ja.md`, `docs/tutorial/04_parallel.md`, `docs/tutorial/04_parallel_ja.md`, `docs/tutorial/05_artifacts.md`, `docs/tutorial/05_artifacts_ja.md`, `docs/tutorial/06_errors.md`, `docs/tutorial/06_errors_ja.md`, `docs/tutorial/08_control.md`, `docs/tutorial/08_control_ja.md`, `docs/plan.md`, `docs/delta/DR-20260312-tutorial-tone-refresh.md`
- AC達成状況: AC-01〜AC-04 PASS

## 検証記録
- verify要約: tutorial 差分確認で導線と表現整理を確認し、`validate_delta_links.js` PASS、`check_code_size.js` PASS（既存 WARN 3件）を確認
- 主要な根拠: `docs/tutorial/02*.md`, `docs/tutorial/03*.md`, `docs/tutorial/04*.md`, `docs/tutorial/05*.md`, `docs/tutorial/06*.md`, `docs/tutorial/08*.md`

## 未解決事項
- なし

## 次のdeltaへの引き継ぎ（任意）
- Seed-01: tutorial 内のサンプルコード自体を plug-in-first の複数ファイル例へ寄せる場合は、学習コストとのバランスを見ながら別 delta で扱う
