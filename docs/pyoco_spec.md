# pyoco — 全体要件（最終版）

## 0) アイデンティティ / 世界観
- **読み**: ぴょこ（pyoco）  
- **トーン**: *軽量・可愛いのに実用的*  
- **トレース表現**: “**ぴょこぴょこ進む**”感じのアニメ／記号（CLI/ログで表現）  
- **モード**:  
  - `cute` … 絵文字・アスキーアート・短い擬音（既定はON）  
  - `non-cute` … 運用向けの無装飾ロギング（CI/本番用）

## 1) 位置づけ
- **目的**: Pythonだけで軽快に回せるDAGワークフローエンジン  
- **DSL**: **illumo-flowと完全互換**（強い制約）
- **構成**:
  - `pyoco` … コア（DAG実行＋Traceコア＋設定/検証）
  - `pyoco-otel` … OTEL Trace backend（任意）

## 2) DSL（互換仕様）
- `>>` 逐次、`&` 並列（AND-join）、`|` 分岐（OR）
- 例: `A >> (B & C) >> D`
- ループ等の将来拡張は illumo-flow と同時リリース

## 3) 実行エンジン
- DAG解析（到達性/トポ順）＋依存解消ノードの並列実行（スレッド; 将来プロセス）
- 失敗ポリシー: `fail=stop|isolate|retry`（タスク単位で設定可）
- リトライ/タイムアウト（タスク単位: `retries`, `timeout_sec`）

## 4) Trace（コア機能・軽量）
- 抽象I/F: `TraceBackend`（`on_flow_start/end`, `on_node_start/end/error`）
- 標準実装: **ConsoleTraceBackend**
  - `cute` モード例:
    - start: `🐇 pyoco > start node=A`
    - hop:   `🐾 A → B & C`（進捗は「ぴょこ」風の短いアニメ/記号）
    - end:   `🥕 done node=B (42 ms)`
  - `non-cute` モード例:
    - `INFO pyoco start node=A`
    - `INFO pyoco end node=B dur_ms=42`
- 切替:
  - CLI: `--trace --cute` / `--trace --non-cute`
  - API: `trace_backend=ConsoleTraceBackend(style="cute"|"plain")`
- 拡張: `pyoco-otel` で OTEL Export（別パッケージ、任意）

## 5) Context中心データモデル
- `ctx` の基本構造: `params`, `env`, `results`, `scratch`, `artifacts`, `run`
- 既定保存: `ctx.results.<NodeName>` に各ノードの出力を自動格納
- セレクタ（参照）: `$ctx.*`, `$flow.*`, `$env.*`, `$node.<Name>.output`
- 追加保存（ターゲット）: `save:` に `ctx:<path>` / `artifact:<name>` を指定
- 大きな成果物はファイル出力＋`ctx.artifacts.*` に（path/sha256等）

## 6) 設定ファイル（YAML; MVP）
```yaml
version: 1
flows:
  main:
    graph: |
      A >> (B & C)
    defaults:
      x: 1

discovery:
  entry_points: ["pyoco.tasks"]
  packages: ["myproject.tasks"]
  glob_modules: ["jobs.*"]

tasks:
  A:
    callable: myproject.tasks:A
    inputs:
      x: $flow.x
    save:
      - ctx:data.a_value

  B:
    callable: myproject.tasks:B
    inputs:
      x: $node.A.output

  C:
    callable: myproject.tasks:C
    inputs:
      x: $node.A.output

runtime:
  expose_env: ["OPENAI_API_KEY"]
```

## 7) 自動検出（Discovery）
- 二系統のタスク定義を検出:
  - `@task` デコレータ付与関数（`__pyoco_task__=True`）
  - `Task` 抽象クラス実装（`run(ctx, **kwargs)` 必須）
- 取得元: `entry_points: "pyoco.tasks"`, `packages`, `modules`, `glob_modules`
- 衝突ルール: 設定で明示指定があれば**明示勝ち**、なければ最初発見を採用（`--strict`でエラー化）

## 8) 検証（`pyoco check`）
- callable import解決
- **シグネチャ照合**（`ctx`除く必須引数が `inputs` で満たされる／未知キー検出）
- **到達性チェック**（`$node.X.output` が先行ノードか）
- リテラル値のみ緩い型チェック（型ヒントあれば）

## 9) Python API / タスク定義
```python
from pyoco import task, Flow, run

@task
def A(ctx, x:int)->int: return x+1
@task
def B(ctx, x:int)->int: return x*2
@task
def C(ctx, x:int)->int: return x-3

flow = Flow() >> A >> (B & C)

if __name__ == "__main__":
    res = run(flow, params={"x":1}, trace=True, cute=True)
    print(res)
```
- `(B & C)` 合流入力の既定: `{ "B": b_out, "C": c_out }` を次ノードへ  
  ※ 実務は `inputs` 明示推奨

## 10) CLI
- 実行: `pyoco run --config flow.yaml --flow main --trace --cute`
- 検証: `pyoco check --config flow.yaml`
- 一覧: `pyoco list-tasks --config flow.yaml`
- 直実行: `pyoco run path/to/flow.py --flow main`

## 11) エラーハンドリング
- タスク単位: `retries`, `timeout_sec`, `fail_policy`
- フロー単位: 失敗時は既定 `stop`、将来 `--resume` を検討

## 12) セキュリティ/サンドボックス
- ローカル信頼環境前提。サンドボックスは将来対応
- `$env` は読み取り専用。`runtime.expose_env` で許可制

## 13) 非機能
- `pip install pyoco` で完結
- READMEサンプルで即動作
- 各タスクは普通の関数としてテスト可能
- **かわいいけど現場投入OK**

## 14) ブランディング / 体験
- **かわいさON (既定)**:
  - うさぎ/足跡/にんじん絵文字＋短い擬音（1行ログ）
  - 例: `🐇 hop A`, `🐾 fanout B & C`, `🥕 done C (67 ms)`
- **運用モード**:
  - `style=plain` で絵文字なしログ
- **ロゴ/マスコット**:
  - うさぎ＋`>` モチーフ（「>>」と「&」の形）
- **設定**:
  - 環境変数: `PYOCO_STYLE=cute|plain`
  - CLI優先 > env > config

## 15) パッケージ構成
```
pyoco/
  __init__.py
  dsl/
  core/
  trace/
  discovery/
  cli/
  schemas/
pyoco-otel/
  backends/otel.py
```

## 16) 移行メモ
- 旧 `pluggy` → 新 `pyoco`
- `"pluggy.tasks"` → `"pyoco.tasks"`

## 17) MVPチェックリスト
- [ ] DSLパーサ＋DAGランナー
- [ ] `@task` & `Task` 抽象クラス
- [ ] コンソールTrace（cute/plain）
- [ ] Context/Selectors/Save
- [ ] 設定YAML＋CLI
- [ ] Discovery＋衝突ルール
- [ ] リトライ/タイムアウト
- [ ] サンプルflow.yaml/README
