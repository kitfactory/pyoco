# Pyoco

要件とは（レビュー者視点）＋ Given/When/Done ＋ MSG/ERR のID管理  
※I/F詳細・API使用は書かない

# 要件一覧（Requirements）
| ID | 要件（固定書式・正常系のみ） | 関連UC-ID |
|---|---|---|
| REQ-0001 | ユーザーがタスクと依存関係を定義したら、Pyocoはフローを構築する。 | UC-1, UC-2 |
| REQ-0002 | ユーザーがフローを実行したら、依存順にタスクを実行して完了状態を返す。 | UC-1 |
| REQ-0003 | 依存のないタスクが複数ある場合、それらを並列に実行する。 | UC-3 |
| REQ-0004 | 上流タスクの出力やパラメータを下流タスクが参照できる。 | UC-4 |
| REQ-0005 | 実行状況をコンソールへトレース出力する。 | UC-1, UC-2, UC-3 |
| REQ-0006 | 実行中に中断が要求されたら、未開始タスクを停止し実行を終了できる。 | UC-2, UC-3 |
| REQ-0007 | ユーザーがタスク一覧の支援情報を要求したら、利用可能タスクを出力する。 | UC-5 |
| REQ-0008 | ユーザーがタスク詳細の支援情報を要求したら、対象タスクの詳細を出力する。 | UC-5 |
| REQ-0009 | ユーザーがflow.yamlガイドを要求したら、定義方法の情報を出力する。 | UC-5 |
| REQ-0010 | ユーザーがタスクフィルタを指定したら、対象タスクを絞り込む。 | UC-5 |
| REQ-0011 | ユーザーが出力形式/出力先を指定したら、指定形式で出力する。 | UC-5 |
| REQ-0012 | プラグインがタスクメタ情報を提供したら、それを支援情報に反映する。 | UC-5 |
| REQ-0013 | ユーザーがパイプDSLを定義したら、`>>` とTerm規則でフローを構築する。 | UC-1, UC-2 |
| REQ-0014 | ユーザーが `pipe(NAME)` を使ったら、`pipes` の定義を展開して接続する。 | UC-1, UC-2 |
| REQ-0015 | ユーザーが `switch` を使ったら、評価値に応じたbranchを1つ実行する。 | UC-1, UC-2 |
| REQ-0016 | ユーザーが `repeat`/`foreach`/`until` を使ったら、反復実行と集約規則で出力を返す。 | UC-1, UC-2 |
| REQ-0017 | ユーザーが `check --dry-run` を実行したら、DSLの形式検証を行う。 | UC-1, UC-2 |

### [PYOCO-0001] ユーザーがタスクと依存関係を定義したら、Pyocoはフローを構築する。
Given：タスク定義が用意されている  
When：フロー定義を読み込み/評価する  
Done：Flowが生成され、タスクと依存関係が登録される（`run` と `check` は同一の評価規則を用いる）

#### エラー分岐（REQ-0001の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルが読めない/構文不正 | パス/形式を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0002 | 未定義タスク参照 | タスク定義/graphを修正する | MSG-PYOCO-0006 |

### [PYOCO-0002] ユーザーがフローを実行したら、依存順にタスクを実行して完了状態を返す。
Given：Flowが構築済みである  
When：フロー実行を開始する  
Done：依存順にタスクが実行され、完了状態が返る

#### エラー分岐（REQ-0002の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0003 | 依存関係が循環/デッドロック | 依存関係を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0004 | タスク処理が例外で失敗 | タスク実装を修正する | MSG-PYOCO-0005 |
| ERR-PYOCO-0005 | タスクがタイムアウト | タイムアウトや処理を調整する | MSG-PYOCO-0005 |

### [PYOCO-0003] 依存のないタスクが複数ある場合、それらを並列に実行する。
Given：独立タスクが複数存在する  
When：フローを実行する  
Done：独立タスクが並列に実行される

#### エラー分岐（REQ-0003の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0004 | タスク処理が例外で失敗 | タスク実装を修正する | MSG-PYOCO-0005 |
| ERR-PYOCO-0005 | タスクがタイムアウト | タイムアウトや処理を調整する | MSG-PYOCO-0005 |

### [PYOCO-0004] 上流タスクの出力やパラメータを下流タスクが参照できる。
Given：上流の出力/パラメータが存在する  
When：下流タスクが参照を行う  
Done：正しい値が解決され、下流に渡される（参照式の構文不正は内容が分かる例外で通知される）

#### エラー分岐（REQ-0004の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0006 | 参照先が存在しない/参照式が不正 | 入力参照を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0007 | 成果物の保存に失敗 | パス/権限を修正する | MSG-PYOCO-0006 |

### [PYOCO-0005] 実行状況をコンソールへトレース出力する。
Given：フロー実行が開始されている  
When：タスクが開始/終了/失敗する  
Done：実行状況がコンソールへ出力される（並列時もタスク単位のログ帰属が維持される）

#### エラー分岐（REQ-0005の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0004 | タスク処理が例外で失敗 | タスク実装を修正する | MSG-PYOCO-0005 |

### [PYOCO-0006] 実行中に中断が要求されたら、未開始タスクを停止し実行を終了できる。
Given：実行中のフローが存在する  
When：中断要求が発生する  
Done：未開始タスクが停止され、実行が終了する

#### エラー分岐（REQ-0006の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0008 | 中断対象が存在しない | 実行中のフローを確認する | MSG-PYOCO-0007 |

### [PYOCO-0007] ユーザーがタスク一覧の支援情報を要求したら、利用可能タスクを出力する。
Given：config/プラグインが読み込める  
When：タスク一覧の支援情報を要求する  
Done：name/summary/inputs/outputs を含むタスク一覧が、origin でグルーピングされ各グループ内 name 昇順で指定形式に出力される

#### エラー分岐（REQ-0007の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルが読めない/構文不正 | パス/形式を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0009 | 出力形式が不正 | formatを修正する | MSG-PYOCO-0011 |
| ERR-PYOCO-0010 | 一致するタスクがない | 条件を修正する | MSG-PYOCO-0012 |
| ERR-PYOCO-0011 | 出力ファイル書き込み失敗 | パス/権限を修正する | MSG-PYOCO-0013 |
| ERR-PYOCO-0012 | フィルタが不正 | フィルタ条件を修正する | MSG-PYOCO-0014 |
| ERR-PYOCO-0013 | 必須メタ情報が欠落 | プラグイン/メタ情報を修正する | MSG-PYOCO-0015 |

### [PYOCO-0008] ユーザーがタスク詳細の支援情報を要求したら、対象タスクの詳細を出力する。
Given：config/プラグインが読み込める  
When：タスク詳細の支援情報を要求する  
Done：name/summary/inputs/outputs を含むタスク詳細が指定形式で出力される

#### エラー分岐（REQ-0008の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルが読めない/構文不正 | パス/形式を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0009 | 出力形式が不正 | formatを修正する | MSG-PYOCO-0011 |
| ERR-PYOCO-0010 | 一致するタスクがない | タスク名を修正する | MSG-PYOCO-0012 |
| ERR-PYOCO-0011 | 出力ファイル書き込み失敗 | パス/権限を修正する | MSG-PYOCO-0013 |
| ERR-PYOCO-0012 | フィルタが不正 | フィルタ条件を修正する | MSG-PYOCO-0014 |
| ERR-PYOCO-0013 | 必須メタ情報が欠落 | プラグイン/メタ情報を修正する | MSG-PYOCO-0015 |

### [PYOCO-0009] ユーザーがflow.yamlガイドを要求したら、定義方法の情報を出力する。
Given：config/プラグインが読み込める  
When：flow.yamlガイドの支援情報を要求する  
Done：flow.yamlのテンプレ/graph記法/入力参照ルールを含むガイドが指定形式で出力される（入力参照は $ctx.params を基本とし、上書き回避/明示的な上流出力は $node.<task>.output を使う）

#### エラー分岐（REQ-0009の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルが読めない/構文不正 | パス/形式を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0009 | 出力形式が不正 | formatを修正する | MSG-PYOCO-0011 |
| ERR-PYOCO-0011 | 出力ファイル書き込み失敗 | パス/権限を修正する | MSG-PYOCO-0013 |

### [PYOCO-0010] ユーザーがタスクフィルタを指定したら、対象タスクを絞り込む。
Given：タスク一覧/詳細の支援情報を生成する  
When：name/origin/tag のフィルタを指定する  
Done：条件に一致するタスクのみが出力される

#### エラー分岐（REQ-0010の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0010 | 一致するタスクがない | 条件を修正する | MSG-PYOCO-0012 |
| ERR-PYOCO-0012 | フィルタが不正 | フィルタ条件を修正する | MSG-PYOCO-0014 |

### [PYOCO-0011] ユーザーが出力形式/出力先を指定したら、指定形式で出力する。
Given：支援情報の生成要求がある  
When：format と出力先を指定する  
Done：APIは文字列で返し、CLIはstdout/ファイルに出力する

#### エラー分岐（REQ-0011の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0009 | 出力形式が不正 | formatを修正する | MSG-PYOCO-0011 |
| ERR-PYOCO-0011 | 出力ファイル書き込み失敗 | パス/権限を修正する | MSG-PYOCO-0013 |

### [PYOCO-0012] プラグインがタスクメタ情報を提供したら、それを支援情報に反映する。
Given：プラグインがname/summary/inputs/outputsを提供している  
When：支援情報を生成する  
Done：entry point 内で task_info により登録されたメタ情報が支援情報に反映される

#### エラー分岐（REQ-0012の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0013 | 必須メタ情報が欠落 | プラグイン/メタ情報を修正する | MSG-PYOCO-0015 |

### [PYOCO-0013] ユーザーがパイプDSLを定義したら、`>>` とTerm規則でフローを構築する。
Given：flow定義がある  
When：graph文字列を読み込み解析する  
Done：`>>` を唯一の連結演算子として解釈し、Term（Task/pipe/switch/repeat/foreach/until）を左から順に接続してFlowを構築する（`>` は未対応のため構文エラー）

#### エラー分岐（REQ-0013の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルが読めない/構文不正 | パス/形式を修正する | MSG-PYOCO-0006 |
| ERR-PYOCO-0014 | DSL構文が不正 | graphを修正する | MSG-PYOCO-0016 |

### [PYOCO-0014] ユーザーが `pipe(NAME)` を使ったら、`pipes` の定義を展開して接続する。
Given：`pipes` に名前付きパイプが定義されている  
When：`pipe(NAME)` を評価する  
Done：参照先パイプをその場に展開し、前後Termと通常の `>>` 連結規則で接続する（単一行/複数行の定義を同じ規則で扱う）

#### エラー分岐（REQ-0014の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0015 | 未定義参照/循環参照/展開上限超過（深さ128または展開後Term数4096超過） | `pipes` 定義を修正する | MSG-PYOCO-0017 |

### [PYOCO-0015] ユーザーが `switch` を使ったら、評価値に応じたbranchを1つ実行する。
Given：`switch(on=..., cases=..., default=任意)` が定義されている  
When：`on` の値を評価する  
Done：一致したcase branchを1つ実行し、そのbranchの最終出力をswitch出力として返す（一致なしでdefault省略時はエラー）

#### エラー分岐（REQ-0015の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0014 | switchの構文（case/default表現）が不正 | graphを修正する | MSG-PYOCO-0016 |
| ERR-PYOCO-0016 | case未一致かつdefault未定義 | switch定義を修正する | MSG-PYOCO-0018 |

### [PYOCO-0016] ユーザーが `repeat`/`foreach`/`until` を使ったら、反復実行と集約規則で出力を返す。
Given：反復Termが定義されている  
When：反復Termを実行する  
Done：反復種別ごとの規則でbodyを実行し、collect規則で出力を返す（既定collectは repeat=list, foreach=list, until=last。collect候補は list/last/first/flatten。`item`/`index` 名の衝突はユーザー自己管理とする）

#### エラー分岐（REQ-0016の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0017 | 反復設定が不正（count<0、max_iter<1、foreachのoverがiterableでない等） | 反復設定を修正する | MSG-PYOCO-0019 |
| ERR-PYOCO-0018 | collect指定が未対応 | collectを修正する | MSG-PYOCO-0020 |

### [PYOCO-0017] ユーザーが `check --dry-run` を実行したら、DSLの形式検証を行う。
Given：flow定義がある  
When：`check --dry-run` を実行する  
Done：DSLの形式のみを検証する（構文、Term種別、`pipes` 参照の存在/循環/上限、switchのdefault省略警告、反復引数の形式）。式や外部データの実評価は行わない

#### エラー分岐（REQ-0017の枝番）
| ERR-ID | 発生条件 | ユーザーアクション | 関連MSG-ID |
|---|---|---|---|
| ERR-PYOCO-0014 | DSL構文が不正 | graphを修正する | MSG-PYOCO-0016 |
| ERR-PYOCO-0015 | `pipe(NAME)` 参照が不正 | `pipes` 定義を修正する | MSG-PYOCO-0017 |
| ERR-PYOCO-0017 | 反復設定の形式が不正 | 反復設定を修正する | MSG-PYOCO-0019 |
| ERR-PYOCO-0018 | collect指定が未対応 | collectを修正する | MSG-PYOCO-0020 |

## メッセージID管理（MSG-xxxx）
| ID | 文面テンプレ | 出力先 | 発生条件 | 関連REQ/ERR |
|---|---|---|---|---|
| MSG-PYOCO-0001 | pyoco start flow={flow} run_id={run_id} | コンソール | 実行開始 | REQ-0005 |
| MSG-PYOCO-0002 | start node={node} | コンソール | タスク開始 | REQ-0005 |
| MSG-PYOCO-0003 | done node={node} ({duration_ms} ms) | コンソール | タスク完了 | REQ-0005 |
| MSG-PYOCO-0004 | done flow={flow} | コンソール | フロー完了 | REQ-0005 |
| MSG-PYOCO-0005 | error node={node} {error} | コンソール | タスク失敗 | ERR-PYOCO-0004/0005 |
| MSG-PYOCO-0006 | Error: {error} | コンソール | 構成/実行の一般エラー | ERR-PYOCO-0001/0002/0003/0006/0007 |
| MSG-PYOCO-0007 | Ctrl+C detected. Cancelling active runs... | コンソール | 中断要求 | REQ-0006/ERR-PYOCO-0008 |
| MSG-PYOCO-0011 | Invalid format: {format} | コンソール | format不正 | ERR-PYOCO-0009 |
| MSG-PYOCO-0012 | Task not found: {name} | コンソール | 一致するタスクなし | ERR-PYOCO-0010 |
| MSG-PYOCO-0013 | Failed to write output: {path} | コンソール | 出力失敗 | ERR-PYOCO-0011 |
| MSG-PYOCO-0014 | Invalid filter: {filter} | コンソール | フィルタ不正 | ERR-PYOCO-0012 |
| MSG-PYOCO-0015 | Missing task metadata: {name} fields={fields} | コンソール | 必須メタ情報欠落 | ERR-PYOCO-0013 |
| MSG-PYOCO-0016 | Invalid DSL syntax: {detail} | コンソール | DSL構文不正 | ERR-PYOCO-0014 |
| MSG-PYOCO-0017 | Invalid pipe reference: {name} | コンソール | pipe参照不正 | ERR-PYOCO-0015 |
| MSG-PYOCO-0018 | Switch no match without default: {value} | コンソール | switch未一致かつdefaultなし | ERR-PYOCO-0016 |
| MSG-PYOCO-0019 | Invalid loop config: {detail} | コンソール | 反復設定不正 | ERR-PYOCO-0017 |
| MSG-PYOCO-0020 | Invalid collect mode: {mode} | コンソール | collect不正 | ERR-PYOCO-0018 |

## エラーID管理（ERR-xxxx）
| ID | 原因 | 検出条件 | ユーザーアクション | 再試行可否 | 関連MSG-ID | 関連REQ |
|---|---|---|---|---|---|---|
| ERR-PYOCO-0001 | 定義ファイルの読み込み失敗 | 読み込み/解析に失敗 | パス/形式を修正する | 可 | MSG-PYOCO-0006 | REQ-0001/0007/0008/0009 |
| ERR-PYOCO-0002 | 未定義タスク参照 | graph参照が未定義 | タスク定義/graphを修正する | 可 | MSG-PYOCO-0006 | REQ-0001 |
| ERR-PYOCO-0003 | 依存関係の循環/デッドロック | 実行中に進行不能 | 依存関係を修正する | 可 | MSG-PYOCO-0006 | REQ-0002/0003 |
| ERR-PYOCO-0004 | タスク処理の例外 | タスク実行で例外発生 | タスク実装を修正する | 可 | MSG-PYOCO-0005 | REQ-0002/0003/0005 |
| ERR-PYOCO-0005 | タスクのタイムアウト | timeout超過 | タイムアウトや処理を調整する | 可 | MSG-PYOCO-0005 | REQ-0002/0003 |
| ERR-PYOCO-0006 | 入力参照の欠落/参照式不正 | 参照解決に失敗 | 入力参照を修正する | 可 | MSG-PYOCO-0006 | REQ-0004 |
| ERR-PYOCO-0007 | 成果物保存の失敗 | ファイルI/Oで失敗 | パス/権限を修正する | 可 | MSG-PYOCO-0006 | REQ-0004 |
| ERR-PYOCO-0008 | 中断対象なし | 実行中フローが存在しない | 実行中のフローを確認する | 可 | MSG-PYOCO-0007 | REQ-0006 |
| ERR-PYOCO-0009 | 出力形式が不正 | format未対応 | formatを修正する | 可 | MSG-PYOCO-0011 | REQ-0007/0008/0009/0011 |
| ERR-PYOCO-0010 | 一致するタスクなし | name/filtersに一致なし | 条件を修正する | 可 | MSG-PYOCO-0012 | REQ-0007/0008/0010 |
| ERR-PYOCO-0011 | 出力失敗 | ファイル書込失敗 | パス/権限を修正する | 可 | MSG-PYOCO-0013 | REQ-0007/0008/0009/0011 |
| ERR-PYOCO-0012 | フィルタ不正 | 未対応キー/空値 | フィルタ条件を修正する | 可 | MSG-PYOCO-0014 | REQ-0007/0008/0010 |
| ERR-PYOCO-0013 | 必須メタ情報欠落 | name/summary/inputs/outputsの欠落 | プラグイン/メタ情報を修正する | 可 | MSG-PYOCO-0015 | REQ-0007/0008/0012 |
| ERR-PYOCO-0014 | DSL構文不正 | `>>` 連結規則またはTerm構文に違反 | graphを修正する | 可 | MSG-PYOCO-0016 | REQ-0013/0015/0017 |
| ERR-PYOCO-0015 | pipe参照不正 | 未定義参照/循環参照/展開上限超過（深さ128、Term数4096） | `pipes` 定義を修正する | 可 | MSG-PYOCO-0017 | REQ-0014/0017 |
| ERR-PYOCO-0016 | switch未一致 | case未一致かつdefault未定義 | switch定義を修正する | 可 | MSG-PYOCO-0018 | REQ-0015 |
| ERR-PYOCO-0017 | 反復設定不正 | count/max_iter/over等の設定が不正 | 反復設定を修正する | 可 | MSG-PYOCO-0019 | REQ-0016/0017 |
| ERR-PYOCO-0018 | collect不正 | 未対応collect指定 | collectを修正する | 可 | MSG-PYOCO-0020 | REQ-0016/0017 |
