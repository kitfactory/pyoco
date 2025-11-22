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
- **Friendly trace logs**: ターミナルからキュートな（またはプレーンな）ログで実行をステップごとに追跡できます。
- **Parallel Execution**: 独立したタスクを自動的に並列実行します。
- **Artifact Management**: タスクの出力やファイルを簡単に保存・管理できます。

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

## 📚 ドキュメント

- [チュートリアル](docs/tutorial/index.md)
- [ロードマップ](docs/roadmap.md)

## 💖 コントリビューション

プルリクエストをお待ちしています！

---

*Made with 🥕 by the Pyoco Team.*
