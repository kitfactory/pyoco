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

# future
- SupportInfoの出力形式拡張（例: yaml）
- タスクメタ情報の自動抽出（シグネチャ/型注釈）
- 大規模フロー向けの支援情報分割出力

# archive
- [x] 初期のplanテンプレートを配置した
