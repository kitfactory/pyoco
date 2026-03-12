# architecture.md（必ず書く：最新版）
#1.アーキテクチャ概要（構成要素と責務）
- ユーザーコード/CLI: タスク・フロー定義、実行/検証/支援情報取得の入口
- DSL/API: `>>` 固定のパイプDSL（Task/`node_name: task_ref`/pipe/switch/repeat/foreach/until）を解析してDAGを構築
- 実行制御: Engine が依存解決・並列実行・キャンセル・状態更新を担う
- DSL解析: DSLParser が graph を字句解析/構文解析し、Term列ASTへ変換する
- 参照展開: PipeResolver が `pipe(NAME)` を展開し循環/上限（深さ128・Term数4096）を検証する
- 形式検証: DryRunValidator が DSL形式のみを検証（式の実評価は対象外）
- 支援情報生成: SupportInfoService がタスク情報を収集し、SupportInfoRenderer が format 変換
- 実行コンテキスト: Context が params/results/scratch/artifacts を管理（artifactsは慣習的な入れ物）
- ドメインモデル: Task/Flow/RunContext/TaskRecord/TaskInfo/TaskIO/SupportInfo が実行状態とメタ情報を保持
- トレース: TraceBackend (ConsoleTraceBackend) がコンソール出力
- 構成/ディスカバリ: PyocoConfig/TaskLoader/PluginRegistry が設定とタスク登録を担う（`tasks.<local>.use` で公開 task 名をローカル task 名へ束ねる）
- インフラ: ThreadPoolExecutor とファイルI/O（config読み込み/成果物保存/支援情報出力）

#2.concept のレイヤー構造との対応表
（テキスト図示）
[User Code/CLI] -> [Engine/SupportInfoService] -> [Context + File I/O]

| conceptレイヤー | 対応コンポーネント | 主な責務 |
|---|---|---|
| プレゼンテーション層 | Python API（task/Flow/run/support）, CLI | フロー定義・実行・支援情報取得 |
| アプリケーション層 | Engine, TaskLoader, DSLParser, PipeResolver, DryRunValidator, FlowValidator, SupportInfoService, SupportInfoRenderer | 実行制御/DSL解析/形式検証/支援情報生成 |
| ドメイン層 | Task/Flow/RunContext/TaskRecord/TaskInfo/TaskIO, DSLノード（TaskTerm/PipeRefTerm/SwitchTerm/RepeatTerm/ForEachTerm/UntilTerm） | DAG表現とメタ情報管理（TaskTerm は `task_ref` と任意の `node_name` を持つ） |
| インフラ層 | ThreadPoolExecutor, filesystem, yaml, json | 並列実行基盤・入出力 |

#2.1 DSL運用ポリシー
- 互換方針: 互換レイヤは持たず、新DSLパーサを正本とする。
- 演算子方針: 連結は `>>` のみを許可し、`>` は未対応エラーとする。
- 反復集約: 既定collectは `repeat=list`, `foreach=list`, `until=last`。
- 変数衝突: `item`/`index` 名の衝突はユーザー自己管理とし、仕様書に予約語/推奨命名を明記する。
- dry-run方針: 形式検証のみ行い、式や外部データの実評価は行わない。

#3.インターフェース設計（Interface）
### UI/APP境界（ユースケース単位）
#### UC-1: 小規模ETL/前処理をDAGで実行
| 操作/API | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| Engine.run | Flowを実行 | flow: Flow（tasks: set<Task>）, params: dict<str, Any> | Context（results: dict<str, Any>, artifacts: dict<str, Any>, run_context: RunContext） | ERR-PYOCO-0003: 依存循環/デッドロック, ERR-PYOCO-0004: タスク例外, ERR-PYOCO-0005: タイムアウト, ERR-PYOCO-0006: 入力参照不足, ERR-PYOCO-0016: switch未一致 |
| pyoco.run | 簡易実行 | flow: Flow, params: dict<str, Any>, trace: bool, cute: bool | Context | 同上 |

#### UC-2: 手作業手順を再実行可能にする
| 操作/API | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| taskデコレータ | 関数をTaskとして登録 | func: Callable（任意引数, ctx注入可） | TaskWrapper（task: Task） | - |
| Flow.add_task | FlowへTask追加 | task: Task | None | - |
| CLI: run/check | 設定からFlowを構築 | config: file path, flow: str | Flow | ERR-PYOCO-0001: 読み込み不正, ERR-PYOCO-0002: 未定義タスク参照（`use` 含む）, ERR-PYOCO-0014: DSL構文不正, ERR-PYOCO-0015: pipe参照不正, ERR-PYOCO-0017: 反復設定不正, ERR-PYOCO-0018: collect不正（run/check は同一DSL評価規則を使用） |

#### UC-3: 依存のない処理を並列化する
| 操作/API | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| Engine.run（並列実行） | 独立タスクを並列実行 | flow: Flow（独立タスクを含む） | Context | ERR-PYOCO-0004/0005: タスク失敗/タイムアウト |

#### UC-4: タスク成果物を次のタスクに渡す
| 操作/API | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| Task.inputs（参照式） | 上流出力/params/envを参照 | inputs: dict<str, str>（$ctx.params.* を基本、上書き回避/明示的な上流出力は $node.<node>.output、$env.*） | 実行時に解決された値 | ERR-PYOCO-0006: 参照先不存在/参照式の構文不正 |
| Context.save_artifact | 成果物をファイル保存 | name: str, data: Any | path: str | ERR-PYOCO-0007: ファイルI/O失敗 |

#### UC-5: LLM向け支援情報を取得する
| 操作/API | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| CLI: support tasks | タスク一覧の取得 | config: file path, format: "prompt/json/md", output: path?, filters: name/origin/tag? | 支援情報（文字列） | ERR-PYOCO-0001: 読み込み不正, ERR-PYOCO-0009: format不正, ERR-PYOCO-0010: 一致するタスクなし, ERR-PYOCO-0011: 出力失敗, ERR-PYOCO-0012: フィルタ不正, ERR-PYOCO-0013: 必須メタ情報欠落 |
| CLI: support task | タスク詳細の取得 | config: file path, name: str, format: "prompt/json/md", output: path?, filters: origin/tag? | 支援情報（文字列） | ERR-PYOCO-0001, ERR-PYOCO-0009, ERR-PYOCO-0010: 一致するタスクなし, ERR-PYOCO-0011, ERR-PYOCO-0012, ERR-PYOCO-0013 |
| CLI: support guide | flow.yamlガイドの取得 | config: file path, format: "prompt/json/md", output: path? | ガイド（文字列） | ERR-PYOCO-0001, ERR-PYOCO-0009, ERR-PYOCO-0011 |
| pyoco.support.build | 支援情報の取得（API） | kind: "tasks/task/guide", config_path: str, format: "prompt/json/md", filters: SupportFilters | str（format済み文字列） | ERR-PYOCO-0001/0009/0010/0011/0012/0013 |

### 外部I/F（API単位）
#### API: 該当なし
| メソッド | 役割 | 入力（型/主要フィールド/値範囲） | 出力（型/主要フィールド） | 例外（発生条件） |
|---|---|---|---|---|
| - | 外部サービスは持たない | - | - | - |

### 内部I/F（クラス単位）
#### Class: Engine
##### Method: run
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| flow | Flow | DAG定義 | tasksはset<Task> | 必須 |
| params | dict<str, Any> | 実行パラメータ | 任意キー | 任意 |
| run_context | RunContext | 既存run文脈 | 既存run_id利用 | 任意 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| ctx | Context | results, artifacts, run_context |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0003 | Engine.run | 依存循環/デッドロック |
| ERR-PYOCO-0004 | Engine._execute_task | タスク例外 |
| ERR-PYOCO-0005 | Engine.run | タスクタイムアウト |
| ERR-PYOCO-0006 | Context.resolve | 参照先不存在/参照式の構文不正 |

##### Method: cancel
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| run_id | str | 実行ID | UUID形式 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0008 | Engine.cancel | 対象Runなし（通知のみ） |

##### Method: get_run
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| run_id | str | 実行ID | UUID形式 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| run_context | RunContext or None | status, task_records |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

#### Class: SupportInfoService
##### Method: build
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| kind | str | 出力種別 | tasks/task/guide | 必須 |
| config_path | str | configパス | 既存ファイル | 必須 |
| format | str | 出力形式 | prompt/json/md | 必須 |
| filters | SupportFilters | フィルタ条件 | name/origin/tag | 任意 |
| output_path | str | 出力ファイル | 相対/絶対 | 任意 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| content | str | format済み文字列 |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0001 | PyocoConfig.from_yaml | config読込失敗 |
| ERR-PYOCO-0009 | SupportInfoRenderer | format不正 |
| ERR-PYOCO-0010 | SupportInfoService | 一致するタスクなし |
| ERR-PYOCO-0011 | SupportInfoWriter | ファイル書き込み失敗 |
| ERR-PYOCO-0012 | SupportInfoService | フィルタ不正 |
| ERR-PYOCO-0013 | SupportInfoService | 必須メタ情報欠落 |

#### Class: TaskInfoCollector
##### Method: collect
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| config_path | str | configパス | 既存ファイル | 必須 |
| filters | SupportFilters | フィルタ条件 | name/origin/tag | 任意 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| tasks | list<TaskInfo> | name/summary/inputs/outputs（必須） |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0001 | PyocoConfig.from_yaml | config読込失敗 |
| ERR-PYOCO-0012 | TaskInfoCollector | フィルタ不正 |
| ERR-PYOCO-0013 | TaskInfoCollector | 必須メタ情報欠落 |

#### Class: SupportInfoRenderer
##### Method: render
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| kind | str | 出力種別 | tasks/task/guide | 必須 |
| tasks | list<TaskInfo> | タスク情報 | 空配列可（tasks/detail時はoriginでグルーピングされ各グループ内name昇順） | 任意 |
| format | str | 出力形式 | prompt/json/md | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| content | str | 文字列 |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0009 | SupportInfoRenderer | format不正 |

#### Class: SupportInfoWriter
##### Method: write
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| content | str | 出力文字列 | 空可 | 必須 |
| output_path | str | 出力先 | 相対/絶対 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0011 | SupportInfoWriter | ファイル書き込み失敗 |

#### Class: PluginRegistry
##### Method: task_info
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| name | str | タスク名 | 非空 | 必須 |
| summary | str | 概要 | 非空 | 必須 |
| inputs | list<TaskIO> | 入力定義 | name/type/required を含む | 必須 |
| outputs | list<TaskIO> | 出力定義 | name/type/required を含む | 必須 |
| tags | list<str> | タグ | 任意 | 任意 |
| origin | str | 提供元 | 任意 | 任意 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0013 | PluginRegistry.task_info | 必須メタ情報欠落 |

#### Class: Context
##### Method: resolve
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| value | Any | 参照式 or 値 | "$node.*" 等の場合のみ解決 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| resolved | Any | 任意 |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0006 | Context.resolve | 参照先不存在/参照式の構文不正 |

##### Method: save_artifact
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| name | str | 成果物名 | 相対パス可 | 必須 |
| data | Any | 保存内容 | bytes/str/その他 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| path | str | 絶対パス |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0007 | Context.save_artifact | ファイルI/O失敗 |

##### Method: set_result
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| node_name | str | ノード名 | graph 上で一意 | 必須 |
| value | Any | 出力値 | 任意 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: get_result
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| node_name | str | ノード名 | graph 上で一意 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| value | Any or None | 取得値 |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

#### Class: PyocoConfig
##### Method: from_yaml
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| path | str | configパス | 既存ファイル | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| config | PyocoConfig | flow, tasks, runtime |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0001 | PyocoConfig.from_yaml | ファイル/構文エラー |

#### Class: TaskLoader
##### Method: load
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| - | - | - | - | - |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: get_task
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| name | str | タスク名 | 既存名 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| task | Task or None | name, func |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

#### Class: DSLParser
##### Method: parse
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| graph | str | flow.graph文字列 | `>>` 連結のみ許可 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| terms | list<DSLTerm> | TaskTerm/PipeRefTerm/SwitchTerm/RepeatTerm/ForEachTerm/UntilTerm（TaskTerm は `task_ref` と任意の `node_name` を保持） |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0014 | DSLParser.parse | DSL構文不正 |

#### Class: PipeResolver
##### Method: resolve
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| terms | list<DSLTerm> | 解析済みTerm列 | - | 必須 |
| pipes | dict<str, str> | 名前付きパイプ定義 | 単一行/複数行文字列 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| expanded_terms | list<DSLTerm> | `pipe(NAME)` 展開済みTerm列 |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0015 | PipeResolver.resolve | 未定義参照/循環参照/展開上限超過 |

#### Class: DryRunValidator
##### Method: validate
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| terms | list<DSLTerm> | 展開済みTerm列 | - | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| report | ValidationReport | errors, warnings |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| ERR-PYOCO-0014 | DryRunValidator.validate | DSL構文不正 |
| ERR-PYOCO-0017 | DryRunValidator.validate | 反復設定不正 |
| ERR-PYOCO-0018 | DryRunValidator.validate | collect不正 |

#### Class: TraceBackend
##### Method: on_flow_start
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| flow_name | str | フロー名 | 非空 | 必須 |
| run_id | str | 実行ID | UUID | 任意 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: on_flow_end
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| flow_name | str | フロー名 | 非空 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: on_node_start
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| node_name | str | タスク名 | 非空 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: on_node_end
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| node_name | str | タスク名 | 非空 | 必須 |
| duration_ms | float | 実行時間(ms) | >=0 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

##### Method: on_node_error
| 引数 | 型 | 意味 | 値範囲/制約 | 必須 |
|---|---|---|---|---|
| node_name | str | タスク名 | 非空 | 必須 |
| error | Exception | エラー | 任意 | 必須 |

| 戻り値 | 型 | 主要フィールド |
|---|---|---|
| None | None | - |

| 例外 | 発生場所 | 発生原因 |
|---|---|---|
| - | - | - |

#### 依存先I/F（最小契約）
| 依存先 | 最小メソッド | 目的 |
|---|---|---|
| FileSystem | read/write/mkdir | config読み込み・成果物保存・支援情報出力 |
| YAML | safe_load | config解析 |
| JSON | dumps | 支援情報のjson化 |
| Python import system | import_module/entry_points | タスク発見 |

### 型定義（入出力/DTOの主要フィールド）
| 型 | 主要フィールド（値範囲/制約） | 用途 |
|---|---|---|
| Flow | name: str, tasks: set<Task>, _definition: list<DSLNode> | DAG定義 |
| Task | name: str(実行ノード名), func: Callable, dependencies: set<Task>, inputs: dict<str, Any>, outputs: list<str>, retries: int>=0, timeout_sec: float|None, trigger_policy: "ALL/ANY" | タスク定義 |
| RunContext | run_id: str(UUID), status: RunStatus, tasks: dict<str, TaskState>, task_records: dict<str, TaskRecord>, logs: list<dict<str, Any>>（メモリのみ） | 実行状態 |
| TaskRecord | state: TaskState, duration_ms: float|None, error: str|None, output: Any | タスク実行記録 |
| Context | params/results/scratch/artifacts: dict<str, Any>, env: dict<str, str>, artifact_dir: str, run_context: RunContext|None（artifactsは慣習的ラベル） | 実行コンテキスト |
| TaskIO | name: str, type: str, required: bool, constraints: list<str>|None | タスク入出力定義 |
| TaskInfo | name: str, summary: str, inputs: list<TaskIO>, outputs: list<TaskIO>, origin: str|None, tags: list<str>|None | タスクメタ情報（必須: name/summary/inputs/outputs） |
| SupportFilters | name: list<str>|None, origin: list<str>|None, tag: list<str>|None | タスク絞り込み |
| SupportInfo | kind: str, format: str, content: str, filters: SupportFilters | 支援情報出力 |
| PyocoConfig | version: int, flow: FlowConfig|None, tasks: dict<str, TaskConfig> | 設定全体 |
| FlowConfig | graph: str, defaults: dict<str, Any> | フロー設定（単一） |
| TaskConfig | use: str|None, callable: str|None, inputs: dict<str, Any>, outputs: list<str> | タスク設定 |
| RuntimeConfig | expose_env: list<str> | env公開設定 |

#4.主要フロー設計（成功/失敗）
| フロー | 成功条件 | 失敗条件 | 例外時の動作 |
|---|---|---|---|
| Python APIでフロー実行 | 全タスク完了しstatus=COMPLETED | 依存循環/タスク例外/タイムアウト | ERR-PYOCO-0003/0004/0005 を返し実行停止 |
| CLIでローカル実行 | config読込→Flow構築→実行完了（run/checkで同一評価規則） | config読込失敗/Flow未定義/評価失敗/未定義タスク参照 | ERR-PYOCO-0001/0002 を表示しexit code=1 |
| キャンセル | 実行中タスク完了後、次タスク遷移前に未開始タスクをCANCELLEDにして実行終了 | 実行中フローなし | ERR-PYOCO-0008 を通知し終了 |
| 支援情報（tasks/detail/guide）生成 | format済み文字列を生成 | format不正/一致するタスクなし/出力失敗/フィルタ不正/必須メタ情報欠落 | ERR-PYOCO-0009/0010/0011/0012/0013 を通知し終了 |

#5.データ設計（永続化・整合性・マイグレーション）
| データ | 永続化 | 整合性 | マイグレーション |
|---|---|---|---|
| Flow/Task定義 | なし（メモリ） | 依存が循環しない | 不要 |
| RunContext/TaskRecord | なし（メモリ） | run_id一意 | 不要 |
| Context.results/scratch/artifacts | なし（メモリ） | ノード名で整合 | 不要 |
| Artifactファイル | ファイルシステム（任意） | path一意 | 不要 |
| TaskInfo/TaskIO | なし（メモリ） | name必須、inputs/outputs必須 | 不要 |
| SupportInfo出力 | 文字列/ファイル（任意） | formatに準拠 | 不要 |
| Config(YAML) | 読込のみ | schemaに従う | 不要 |

#6.設定：場所／キー／既定値
| 項目 | 場所 | キー | 既定値 |
|---|---|---|---|
| フロー設定ファイル | CLI | --config | なし（必須） |
| フロー名 | CLI | - | main（固定） |
| パラメータ上書き | CLI | --param | なし |
| トレーススタイル | ENV/CLI | PYOCO_CUTE / --cute / --non-cute | cute |
| artifact_dir | Context初期化 | artifact_dir | ./artifacts |
| 支援情報種別 | CLI | support tasks/task/guide | なし（必須） |
| 支援情報形式 | CLI | --format | prompt |
| 支援情報出力先 | CLI | --output | stdout |
| 支援情報フィルタ | CLI | --name/--origin/--tag | なし |

#7.依存と拡張点（Extensibility）
| 依存 | 目的 | 拡張点 |
|---|---|---|
| Python標準ライブラリ | 並列/入出力/シグナル | 置換不可 |
| PyYAML | config読み込み | schema拡張 |
| TraceBackend | トレース出力 | カスタムTraceBackend実装 |
| TaskLoader/PluginRegistry | タスク発見 | entry point (pyoco.tasks) 内で task_info によりメタ情報登録 |
| SupportInfoRenderer | 支援情報の出力形式 | prompt/json/md の追加形式 |

#7.5.依存関係（DI）
（テキスト図示）
Engine -> TraceBackend
SupportInfoService -> TaskInfoCollector -> TaskLoader
SupportInfoService -> SupportInfoRenderer
CLI -> PyocoConfig, TaskLoader, Engine, SupportInfoService

| クラス | コンストラクタDI（依存先） | 目的 |
|---|---|---|
| Engine | TraceBackend | トレース出力切替 |
| TaskLoader | PyocoConfig | タスク探索設定 |
| SupportInfoService | TaskInfoCollector/SupportInfoRenderer | 支援情報生成 |
| ConsoleTraceBackend | - | コンソール出力 |

#8.エラーハンドリング設計（冪等性/リトライ/タイムアウト/部分失敗）
| 事象 | 発生場所 | 発生原因 | 方針 | 備考 |
|---|---|---|---|---|
| 設定/定義読み込み失敗 | CLI/Config | ファイル不存在/構文不正 | ERR-PYOCO-0001 を表示し停止 | 再試行は修正後 |
| 未定義タスク参照 | FlowValidator/TaskLoader | graph参照が未定義 | ERR-PYOCO-0002 を表示し停止 | 参照修正 |
| 依存循環/デッドロック | Engine.run | 実行不能な依存 | ERR-PYOCO-0003 で停止 | 依存修正 |
| タスク実行例外 | Engine._execute_task | ユーザー関数例外 | ERR-PYOCO-0004 を出力し停止 | fail_policy=stop |
| タスクタイムアウト | Engine.run | timeout_sec超過 | ERR-PYOCO-0005 を出力し停止 | timeout調整 |
| 入力参照不正 | Context.resolve | 参照先不存在/参照式の構文不正 | ERR-PYOCO-0006 を出力し停止 | 入力修正 |
| 成果物保存失敗 | Context.save_artifact | 権限/パス不正 | ERR-PYOCO-0007 を出力し停止 | パス修正 |
| キャンセル対象なし | Engine.cancel | 該当run無し | ERR-PYOCO-0008 を通知 | 影響なし |
| format不正 | SupportInfoRenderer | 未対応format | ERR-PYOCO-0009 を通知 | format修正 |
| 一致するタスクなし | SupportInfoService | name/filtersに一致なし | ERR-PYOCO-0010 を通知 | 条件修正 |
| 出力失敗 | SupportInfoWriter | 書込エラー | ERR-PYOCO-0011 を通知 | パス修正 |
| フィルタ不正 | SupportInfoService | 未対応キー/空値 | ERR-PYOCO-0012 を通知 | フィルタ修正 |
| 必須メタ情報欠落 | SupportInfoService/PluginRegistry | name/summary/inputs/outputs欠落 | ERR-PYOCO-0013 を通知 | メタ情報修正 |

#9.セキュリティ設計（秘密情報・最小権限・ログ方針）
| 観点 | 方針 |
|---|---|
| 認証/認可 | 対象外（ローカル実行） |
| 秘密情報 | params/envに保持、永続化しない。支援情報には秘密情報を含めない。 |
| ログ方針 | コンソール出力のみ、永続化しない |

#10.観測性（ログ/診断：doctor/status/debug）
| 種別 | 内容 | 出力先 |
|---|---|---|
| 実行トレース | flow/node開始/終了/エラー | コンソール |
| run_id | 実行IDの表示 | コンソール |
| 支援情報 | tasks/detail/guide の生成結果 | stdout/ファイル |

## 例外ハンドリング方針（UI/ユースケース層）
| UC | 例外 | 表示/通知 | エラーID/コード方針 | 関連spec ERR-ID |
|---|---|---|---|---|
| UC-1 | 依存循環/タスク例外/タイムアウト | エラーメッセージ出力 | ERR-PYOCO-0003/0004/0005 | ERR-PYOCO-0003/0004/0005 |
| UC-2 | 定義不正/未定義タスク参照 | エラーメッセージ出力 | ERR-PYOCO-0001/0002 | ERR-PYOCO-0001/0002 |
| UC-3 | タスク失敗/タイムアウト | エラーメッセージ出力 | ERR-PYOCO-0004/0005 | ERR-PYOCO-0004/0005 |
| UC-4 | 入力参照不足/保存失敗 | エラーメッセージ出力 | ERR-PYOCO-0006/0007 | ERR-PYOCO-0006/0007 |
| UC-5 | format不正/一致するタスクなし/出力失敗/フィルタ不正/必須メタ欠落 | エラーメッセージ出力 | ERR-PYOCO-0009/0010/0011/0012/0013 | ERR-PYOCO-0009/0010/0011/0012/0013 |

#11.テスト設計（単体/統合/E2E、モック方針）
| 種別 | 対象 | 方針 |
|---|---|---|
| 単体 | Context.resolve/save_artifact | 参照解決/ファイルI/Oを分離 |
| 単体 | Engine.run | 依存解決/並列実行/タイムアウト |
| 単体 | SupportInfoService/Renderer | format/filters/一致するタスクなし/メタ欠落の検証 |
| 統合 | CLIローカル実行 | config読み込み→実行完了 |
| 統合 | support CLI | tasks/detail/guide の出力検証 |
| 統合 | プラグインメタ情報 | entry point 由来のTaskInfo反映 |

#12.配布・実行形態（インストール/更新/互換性/破壊的変更）
- pip配布のライブラリとして提供
- ローカル環境で更新（破壊的変更は最小化）

#13.CLI：コマンド体系／引数／出力／exit code
- run: フロー実行（--config 必須, --param, --cute/--non-cute）
- check: フロー検証（--config 必須, --dry-run, --json）
- list-tasks: 利用可能タスク一覧（--config 必須）
- plugins: プラグイン一覧/検証（list, lint, --json）
- support tasks: タスク一覧の支援情報（--config 必須, --format, --output, --name/--origin/--tag）
- support task: タスク詳細の支援情報（--config 必須, --name 必須, --format, --output, --origin/--tag）
- support guide: flow.yamlガイド（--config 必須, --format, --output）
- server/worker/runs はアーカイブ済みのため本ドキュメントの対象外
- 出力: コンソール（トレース/結果/エラー/支援情報）
- exit code: 0=成功, 1=一般エラー, 2=検証エラー（dry-run時）
