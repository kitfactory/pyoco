# 🐇 Pyoco

**pyoco は、シンプルなタスクベースのワークフローを定義・実行するための、最小限で純粋な Python 製 DAG エンジンです。**

## 概要

Pyoco は、Airflow などの大規模なワークフローエンジンよりもはるかに小さく、軽量で、依存関係が少ないように設計されています。ローカル開発や単一マシンでの実行に最適化されています。

デコレータとシンプルな API を使用して、タスクとその依存関係を完全に Python コードで定義できます。複雑な設定ファイルや外部データベースは必要ありません。

フルスタックのワークフローエンジンでは大げさすぎるような、小さなジョブ、開発環境、個人プロジェクトに最適です。

## ✨ 特徴

- **Pure Python**: 外部サービスや重い依存関係は不要です。
- **Minimal DAG model**: タスクと依存関係をコードで直接定義します。
- **Task-oriented**: 読みやすく保守しやすい「小さなワークフロー」に焦点を当てています。
- **Graph DSL controls**: `flow.yaml` で `>>` / `pipe` / `switch` / `repeat` / `foreach` / `until` を使って制御フローを記述できます。
- **Friendly trace logs**: ターミナルからキュートな（またはプレーンな）ログで実行をステップごとに追跡できます。
- **Parallel Execution**: 独立したタスクを自動的に並列実行します。
- **Artifact Management**: タスクの出力やファイルを簡単に保存・管理できます。
- **Observability**: ユニークな Run ID と詳細な状態遷移で実行を追跡できます。
- **Control**: `Ctrl+C` で実行中のワークフローを安全にキャンセルできます。

## 📦 インストール

```bash
pip install pyoco
```

## 🚀 使い方

純粋な Python コードだけでワークフローを定義する最小限の例です。

```python
from pyoco import task
from pyoco.core.models import Flow
from pyoco.core.engine import Engine

@task
def fetch_data(ctx):
    print("🐰 Fetching data...")
    return {"id": 1, "value": "carrot"}

@task
def process_data(ctx, data):
    print(f"🥕 Processing: {data['value']}")
    return data['value'].upper()

@task
def save_result(ctx, result):
    print(f"✨ Saved: {result}")

# フローを定義
flow = Flow(name="hello_pyoco")
flow >> fetch_data >> process_data >> save_result

# 入力を配線（この例では明示的に指定）
process_data.task.inputs = {"data": "$node.fetch_data.output"}
save_result.task.inputs = {"result": "$node.process_data.output"}

if __name__ == "__main__":
    engine = Engine()
    engine.run(flow)
```

実行コマンド:

```bash
python examples/hello_pyoco.py
```

出力結果:

```
🐇 pyoco > start flow=hello_pyoco
🏃 start node=fetch_data
🐰 Fetching data...
✅ done node=fetch_data (0.30 ms)
🏃 start node=process_data
🥕 Processing: carrot
✅ done node=process_data (0.23 ms)
🏃 start node=save_result
✨ Saved: CARROT
✅ done node=save_result (0.30 ms)
🥕 done flow=hello_pyoco
```

完全なコードは [examples/hello_pyoco.py](examples/hello_pyoco.py) を参照してください。

## 🧾 flow.yaml の Graph DSL

Pyoco は `flow.yaml` でもワークフローを定義できます。現行DSLは `>>` を基本に、`pipe/switch/repeat/foreach/until` を組み合わせます。

```yaml
version: 1

pipes:
  setup: "prepare >> choose_mode"

tasks:
  prepare:
    callable: "tasks:prepare"
  choose_mode:
    callable: "tasks:choose_mode"
  run_batch:
    callable: "tasks:run_batch"
  process_item:
    callable: "tasks:process_item"
  poll_status:
    callable: "tasks:poll_status"
  finish:
    callable: "tasks:finish"

flow:
  defaults:
    mode: "batch"
    items: ["A", "B", "C"]
    done: false
  graph: |
    pipe(setup)
    >> switch(on={{mode}}){
      batch: repeat(count=2){ run_batch };
      default: run_batch;
    }
    >> foreach(over={{items}}, item=it, index=idx){ process_item }
    >> until(cond={{params.done}}, max_iter=5){ poll_status }
    >> finish
```

- `>>`: 逐次依存
- `pipe(NAME)`: `pipes` で定義したパイプを参照展開
- `switch(on=...){ ... }`: 条件に一致した分岐を1つ実行
- `repeat` / `foreach` / `until`: 反復制御

## 🏗️ アーキテクチャ

Pyoco はシンプルなフローで設計されています:

```
+-----------+        +------------------+        +-----------------+
| User Code |  --->  | pyoco.core.Flow  |  --->  | trace/logger    |
| (Tasks)   |        | (Engine)         |        | (Console/File)  |
+-----------+        +------------------+        +-----------------+
```

1. **User Code**: Python デコレータを使用してタスクとフローを定義します。
2. **Core Engine**: エンジンが依存関係を解決し、タスクを実行します（可能な場合は並列実行）。
3. **Trace**: 実行イベントはトレースバックエンドに送信され、ログ出力されます（キュートまたはプレーン）。

## 🎭 モード

Pyoco には2つの出力モードがあります:

- **Cute Mode** (デフォルト): 絵文字とフレンドリーなメッセージを使用します。ローカル開発や学習に最適です。
- **Non-Cute Mode**: プレーンテキストのログ。CI/CD や本番環境の監視に最適です。

環境変数で切り替えることができます:

```bash
export PYOCO_CUTE=0  # Cuteモードを無効化
```

または CLI フラグを使用します:

```bash
pyoco run --non-cute ...
```

## 🔭 オブザーバビリティ / サーバー（アーカイブ）

観測・サーバー関連のドキュメントはアーカイブ済みで、現在の要件対象外です。  
`docs/archive/observability.md` と `docs/archive/roadmap.md` を参照してください。

## 🌐 分散実行は `pyoco-server` を利用

`pyoco` 本体はローカル/単一マシン実行を主対象にしています。  
複数ワーカーでの分散実行、キューイング、リモート実行管理が必要な場合は、姉妹ライブラリ **`pyoco-server`** を利用してください。

- パッケージ名: `pyoco-server`
- 役割: Pyoco向け NATS/JetStream ベース分散実行バックエンド
- CLI: `pyoco-server`, `pyoco-worker`, `pyoco-client`, `pyoco-server-admin`
- リポジトリ: <https://github.com/kitfactory/pyoco-server>

導入の流れ:
1. サーバー起動: `pyoco-server up`
2. ワーカー起動: `pyoco-worker --tags ...`
3. 実行投入・監視: `pyoco-client submit-yaml`, `pyoco-client watch`

互換メモ:
- `pyoco-server 0.5.x` は `pyoco >= 0.6.2` に依存
- 推奨組み合わせ: `pyoco 0.7.x` + `pyoco-server 0.5.x`

## 🧩 プラグイン

`pyoco.tasks` エントリポイントに Hook (`def register_tasks(registry): ...`) を公開すると、Pyoco が自動でタスクをロードします。**Task サブクラス優先** を推奨します（callable も動きますが警告対象）。`docs/plugins.md` に `PluginRegistry` の使い方、`pyproject.toml` 設定例、`pyoco plugins list` / `pyoco plugins lint` の説明を掲載しています。

**大きなデータについて:** そのままコピーせずハンドルを渡すのが安全です。巨大なテンソル/画像は `ctx.artifacts` や `ctx.scratch` にパスやハンドルを置き、必要なタスクだけが実体化する形にします。遅延パイプライン（例: DataPipe）は、実際に回すタスク（例: 学習タスク）でパイプ構成をログに出し、上流で全量展開しないようにします。

## 🧭 タスク探索（セキュリティ）

探索範囲を `flow.yaml` から指定できると安全性が下がるため、Pyoco は `flow.yaml` の `discovery:` を受け付けません（指定するとエラーになります）。

- **エントリポイント・プラグイン**: `importlib.metadata.entry_points(group="pyoco.tasks")` から自動ロード
- **追加 import（運用側で制御）**: `PYOCO_DISCOVERY_MODULES`（カンマ/空白区切りのモジュール名）を設定。例: `PYOCO_DISCOVERY_MODULES=tasks,myapp.extra_tasks`
- **明示タスク定義**: `flow.yaml` の `tasks.<name>.callable` を基本にする（詳細はチュートリアル参照）

## 📚 ドキュメント

- [チュートリアル](docs/tutorial/index.md)
- [ロードマップ（アーカイブ）](docs/archive/roadmap.md)

## 💖 コントリビューション

プルリクエストをお待ちしています！

---

*Made with 🥕 by the Pyoco Team.*
