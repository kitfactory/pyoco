# 🐇 Pyoco

**pyoco は、シンプルなタスクベースのワークフローを定義・実行するための、最小限で純粋な Python 製 DAG エンジンです。**

## ✨ まず伝えたいこと

- ⚡ **数分で試せます**: 小さなローカル workflow だけで最初の成功体験まで行けます。
- 🧩 **そのまま育てられます**: 再利用したくなったら plug-in + `tasks.<local>.use` に移れます。
- 🪶 **重い前提がありません**: スケジューラ群や外部DBを先に組まなくても始められます。

Pyoco は、Airflow のような大規模ワークフロー基盤よりかなり小さく、ローカル開発・単一マシン実行・「まず動かしたい」ケースに寄せて設計されています。

## 🚦 入口は2つあります

- **最短で試す入口**: 1ファイルだけで書いて、まず Pyoco の実行感を掴む。
- **おすすめの入口**: 再利用するタスクを plug-in として公開し、`flow.yaml` で `tasks.<local_name>.use` に束ねる。

はじめて触るなら、まず最短ルートで1回動かすのが楽です。継続利用するなら、その直後に plug-in ルートへ進むのが自然です。

## ✨ 特徴

- **Pure Python**: 外部サービスや重い依存関係は不要です。
- **Minimal DAG model**: タスクと依存関係をコードで直接定義します。
- **Task-oriented**: 読みやすく保守しやすい「小さなワークフロー」に焦点を当てています。
- **Graph DSL controls**: `flow.yaml` で `>>` / `node_name: task_ref` / `pipe` / `switch` / `repeat` / `foreach` / `until` を使って制御フローを記述できます。
- **Friendly trace logs**: ターミナルからキュートな（またはプレーンな）ログで実行をステップごとに追跡できます。
- **Parallel Execution**: 独立したタスクを自動的に並列実行します。
- **Artifact Management**: タスクの出力やファイルを簡単に保存・管理できます。
- **Observability**: ユニークな Run ID と詳細な状態遷移で実行を追跡できます。
- **Control**: `Ctrl+C` で実行中のワークフローを安全にキャンセルできます。

## 📦 インストール

```bash
pip install pyoco
```

## 🚀 まずは 60 秒で動かす

これは **最短の Hello** です。1ファイルに閉じるので、まず「動く感じ」をすぐ試せます。

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

## 🧭 継続利用するならこの形

再利用したいタスク、共有したいタスク、説明可能な task カタログを作りたいときは、次の形を基本にしてください。

1. Task サブクラスを plug-in パッケージで公開する
2. `vision/image_classify` のような安定した公開名を付ける
3. `flow.yaml` では `tasks.<local_name>.use` でローカル名へ束ねる

これが、現在の Pyoco が **正規ルート** として見せたい使い方です。

## 🧾 flow.yaml の Graph DSL

1ファイル実験を超えていくなら、このモデルを覚えるのが近道です。`flow.yaml` で graph を読みやすく保ち、plug-in 公開名でタスク再利用をきれいに管理できます。

本番寄りのタスク共有では、**Task サブクラスを entry point plug-in として登録し、`flow.yaml` では `tasks.<local_name>.use` で束ねる方法を基本**にしてください。`tasks.<name>.callable` は、ローカルな明示上書きや移行用途向けです。

```yaml
version: 1

tasks:
  prepare:
    use: "demo/prepare"
  choose_mode:
    use: "demo/choose_mode"
  run_batch:
    use: "demo/run_batch"
  process_item:
    use: "demo/process_item"
  poll_status:
    use: "demo/poll_status"
  finish:
    use: "demo/finish"

flow:
  defaults:
    mode: "batch"
    items: ["A", "B", "C"]
    done: false
  graph: |
    prepare
    >> choose_mode
    >> switch(on={{mode}}){
      batch: first_batch: run_batch >> second_batch: run_batch;
      default: run_batch;
    }
    >> foreach(over={{items}}, item=it, index=idx){ process_item }
    >> until(cond={{params.done}}, max_iter=5){ poll_status }
    >> finish
```

- `>>`: 逐次依存
- `node_name: task_ref`: 1つの task 定義を別の実行ノード名で再利用
- `tasks.<local_name>.use`: `demo/run_batch` のような公開 task 名をローカル graph 名へ束ねる
- `pipe(NAME)`: `pipes` で定義したパイプを参照展開
- `switch(on=...){ ... }`: 条件に一致した分岐を1つ実行
- `repeat` / `foreach` / `until`: 反復制御

仕様書に入る前に段階的に試したい場合は、[チュートリアル](docs/tutorial/index_ja.md) から入るのが簡単です。

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
複数ワーカーでの分散実行、キューイング、リモート実行管理が必要な場合は **`pyoco-server`** を利用してください。

- plug-in 形式にする実務上の利点は、task 群をその場のソース断片ではなく wheel として配布しやすいことです。
- `pyoco-server` はその配布モデルと相性がよく、再利用 task を package 化しておくと worker 群へ広げやすくなります。
- リポジトリ: <https://github.com/kitfactory/pyoco-server>
- 導入手順・運用手順・互換情報の詳細は `pyoco-server` 側のドキュメントを参照してください。

## 🧩 プラグイン

`pyoco.tasks` エントリポイントに Hook (`def register_tasks(registry): ...`) を公開すると、Pyoco が自動でタスクをロードします。これを **基本の登録経路** とし、**Task サブクラス優先** を推奨します（callable も動きますが警告対象）。公開名は `vision/image_classify` のような安定名にし、`flow.yaml` では `tasks.<local_name>.use` で束ねます。`docs/plugins.md` に `PluginRegistry` の使い方、`pyproject.toml` 設定例、`pyoco plugins list` / `pyoco plugins lint` の説明を掲載しています。

この経路を推す理由のひとつは、task が package になった時点で `pyoco-server` の worker 群へ version 付き plug-in として配布しやすくなることです。

**大きなデータについて:** そのままコピーせずハンドルを渡すのが安全です。巨大なテンソル/画像は `ctx.artifacts` や `ctx.scratch` にパスやハンドルを置き、必要なタスクだけが実体化する形にします。遅延パイプライン（例: DataPipe）は、実際に回すタスク（例: 学習タスク）でパイプ構成をログに出し、上流で全量展開しないようにします。

## 🧭 タスク探索（セキュリティ）

探索範囲を `flow.yaml` から指定できると安全性が下がるため、Pyoco は `flow.yaml` の `discovery:` を受け付けません（指定するとエラーになります）。

- **エントリポイント・プラグイン**: `importlib.metadata.entry_points(group="pyoco.tasks")` から自動ロード
- **追加 import（運用側で制御）**: `PYOCO_DISCOVERY_MODULES`（カンマ/空白区切りのモジュール名）を設定。例: `PYOCO_DISCOVERY_MODULES=tasks,myapp.extra_tasks`
- **フロー内束ね直し**: 登録済み plug-in task は `tasks.<local_name>.use: "namespace/task_name"` を優先する
- **明示タスク定義**: `flow.yaml` の `tasks.<name>.callable` はローカル上書きや簡易フロー向けに使う

## 📚 ドキュメント

- [チュートリアル](docs/tutorial/index_ja.md)
- [ロードマップ（アーカイブ）](docs/archive/roadmap.md)

## 💖 コントリビューション

プルリクエストをお待ちしています！

---

*Made with 🥕 by the Pyoco Team.*
