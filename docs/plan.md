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

# future
- SupportInfoの出力形式拡張（例: yaml）
- タスクメタ情報の自動抽出（シグネチャ/型注釈）
- 大規模フロー向けの支援情報分割出力

# archive
- [x] 初期のplanテンプレートを配置した
