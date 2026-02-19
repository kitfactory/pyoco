# plan.md（必ず書く：最新版）

# current
- [x] docs/OVERVIEW.md / docs/concept.md / docs/spec.md / docs/architecture.md の現状を確認する
- [x] docs/concept.md の UC-5 例外記述を spec/architecture に合わせて更新する
- [x] SupportInfo用のデータモデル/エラー型を追加する（src/pyoco/core/models.py, src/pyoco/core/exceptions.py）
- [x] SupportInfo用のデータモデル/エラー型の単体テストを追加する（tests/core/test_support_models.py）
- [x] PluginRegistryにtask_info登録と必須メタ検証を追加する（src/pyoco/discovery/plugins.py, src/pyoco/discovery/loader.py）
- [x] PluginRegistryのメタ登録を単体テストする（tests/plugins/test_registry_task_info.py）
- [x] TaskInfoCollector/SupportInfoService/Renderer/Writerを実装する（src/pyoco/support/*.py）
- [x] SupportInfoService/Rendererの単体テストを追加する（tests/support/test_support_info.py）
- [x] CLIにsupport tasks/task/guideを追加する（src/pyoco/cli/main.py, src/pyoco/cli/entry.py, src/pyoco/__init__.py）
- [x] CLI supportコマンドの統合テストを追加する（tests/cli/test_cli_support.py）
- [x] flow.yaml + プラグインメタ情報のE2Eテストを追加する（tests/test_e2e_support_info.py）
- [x] SupportInfoの単体テストを実行する（tests/core/test_support_models.py, tests/support/test_support_info.py）
- [x] CLI supportの統合テストを実行する（tests/cli/test_cli_support.py）
- [x] SupportInfoのE2Eテストを実行する（tests/test_e2e_support_info.py）
- [x] 文書との整合性を確認する（docs/concept.md, docs/spec.md, docs/architecture.md）
- [x] cancel要求時に「次タスク遷移前で停止」する境界キャンセルをEngineへ実装する（src/pyoco/core/engine.py）
- [x] 実行中cancelの境界停止テストを追加する（tests/core/test_engine_cancellation_boundary.py）
- [x] 1〜4の改善方針を文書化する（docs/OVERVIEW.md, docs/spec.md, docs/architecture.md）
- [x] 並列実行時の標準出力/標準エラーをタスク単位で安全に捕捉する（src/pyoco/core/engine.py）
- [x] 並列ログ捕捉の混線防止を単体テストで検証する（tests/core/test_engine_parallel.py）
- [x] 参照式の誤記を内容が分かる例外で通知する（src/pyoco/core/context.py, src/pyoco/core/exceptions.py）
- [x] 参照式の不正フォーマット検出テストを追加する（tests/core/test_context_resolve.py）
- [x] `check` の graph 評価を `run` と同一規則へ統一する（src/pyoco/cli/main.py）
- [x] `check` の評価規則統一をCLIテストで検証する（tests/cli/test_cli.py）
- [x] 旧実装コメント/`pass` の整理で保守性を改善する（src/pyoco/core/models.py, src/pyoco/worker/runner.py）
- [x] 回帰テストを実行して整合性を確認する（tests/core/test_context_resolve.py, tests/core/test_engine_parallel.py, tests/cli/test_cli.py）
- [x] 文書との整合性を最終確認する（docs/spec.md, docs/architecture.md, docs/plan.md）
- [x] ログ捕捉リファクタ計画を作成し作業単位を固定する（docs/plan.md）
- [x] ログ捕捉を専用モジュールへ分離しEngineの隠れ依存を削除する（src/pyoco/core/log_capture.py, src/pyoco/core/engine.py）
- [x] タスク実行時のログ付与処理を共通化して分岐を簡素化する（src/pyoco/core/engine.py）
- [x] リファクタ向け回帰テストを追加する（tests/core/test_log_capture.py, tests/core/test_engine_parallel.py）
- [x] 対象テストと全体テストを実行し文書整合を確認する（tests/core/test_log_capture.py, tests/core/test_engine_parallel.py, docs/plan.md）
- [x] switch/repeat/foreach/until/pipe(NAME) 拡張の適用範囲を整理する（docs/OVERVIEW.md, docs/concept.md, docs/spec.md, docs/architecture.md）
- [x] 互換性方針を固定する（互換レイヤは持たず、新DSLを正として仕様化する）
- [x] 字句解析の実現性スパイクを先行実施する（block構文、YAML複数行、ネスト時のトークン境界を検証）
- [x] 字句解析スパイクの検証結果を文書化する（採用文法/不採用文法/失敗パターンを記録、docs/dsl_lexer_spike.md）
- [x] DSL拡張仕様を文書へ展開する（`>>`固定、Term統一、pipes map、switch/repeat/foreach/until 構文、エラー規約）
- [x] switch仕様を固定する（default省略時は実行時エラー、check時に警告/エラー判定ルールを定義）
- [x] 反復結果の集約仕様を固定する（repeat/foreach/until の collect 既定値と返却型を定義）
- [x] pipe参照展開の安全上限を固定する（展開深さ上限/展開Term上限/循環参照エラー）
- [x] item/index 変数衝突の運用方針を文書化する（自己管理・予約語・推奨命名規則）
- [x] dry-run検証範囲を固定する（形式検証中心、式の実評価は対象外）
- [x] パーサに PipeRefTerm と block 形式の文法を実装する（src/pyoco/dsl/graph.py）
- [x] パーサ拡張の単体テストを追加する（tests/dsl/test_graph.py）
- [x] 実行器に pipe 展開と制御Term実行の統合を実装する（src/pyoco/dsl/graph.py, src/pyoco/core/engine.py, src/pyoco/dsl/nodes.py）
- [x] 実行器拡張の単体テストを追加する（tests/engine/test_switch.py, tests/engine/test_loop_execution.py, tests/core/test_engine_cancellation_boundary.py）
- [x] CLI run/check を新DSL評価へ対応する（src/pyoco/cli/main.py, src/pyoco/worker/runner.py）
- [x] CLI check --dry-run にDSL拡張向け検証を追加する（pipe未定義/循環、switch default、repeat/foreach/until 引数妥当性）
- [x] CLI統合テストを追加する（tests/cli/test_cli.py）
- [x] チュートリアル/README/guide を新DSL表記へ更新する（docs/tutorial/*.md, README.md, README_ja.md, src/pyoco/support/renderer.py）
- [x] DSL拡張のE2Eテストを追加する（tests/test_e2e_*.py）
- [x] 対象テストと回帰テストを実行する（dsl/engine/cli/e2e）
- [x] 文書整合性を最終確認する（docs/concept.md, docs/spec.md, docs/architecture.md, docs/plan.md）

# future
- SupportInfoの出力形式拡張（例: yaml）
- タスクメタ情報の自動抽出（シグネチャ/型注釈）
- 大規模フロー向けの支援情報分割出力

# archive
- [x] 初期のplanテンプレートを配置した
