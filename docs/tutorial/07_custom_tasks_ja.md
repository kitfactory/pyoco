# 7. BaseTask を使ったカスタムタスク

この章は、Pyoco を「ちょっとしたデモ」から「ちゃんと使い続ける project」へ進める章です。再利用タスクの推奨経路として、抽象基底クラス **`BaseTask`** を継承し、それを **plug-in entry point として登録** する方法を学びます。`flow.yaml` では登録済み公開名を `use` で束ねます。

## いつ読む章か？

- 🧩 同じ task を複数の flow で使い回したい
- 📦 task をパッケージとしてきれいに公開したい
- 🧭 `flow.yaml` を読みやすく保ったまま再利用したい
- 🌐 将来的に `pyoco-server` の worker へ同じ task package を配りたい

## なぜ `BaseTask` を使うのか？

- すべてのカスタムタスクに対して明確な契約 (`run(self, ctx)`) を与えます。
- 継承を通じて、複数のタスク間でヘルパーメソッドや状態を共有できます。
- ドキュメントの発見性が向上します（ユーザーは共通の基底クラスがあることを知ることができます）。

## 実装例

Python モジュールを作成します（例: `examples/custom_task_demo.py`）:

```python
# examples/custom_task_demo.py
from pyoco.core.base_task import BaseTask
from pyoco.core.models import TaskIO

class MultiplyTask(BaseTask):
    """入力値を係数で掛け合わせるシンプルなタスク。

    ``run`` メソッドは実行コンテキスト ``ctx`` を受け取ります。
    これにより、``params`` / ``scratch`` や `flow.yaml` から解決された値にアクセスできます。
    """

    def run(self, ctx):
        value = ctx.params.get("start", 1)
        factor = ctx.params.get("multiplier", 2)
        result = value * factor
        return result


def register_tasks(registry):
    registry.task_class(MultiplyTask, name="demo/multiply")
    registry.task_info(
        name="demo/multiply",
        summary="入力値を係数で掛け合わせる。",
        inputs=[
            TaskIO(name="start", type="int", required=False),
            TaskIO(name="multiplier", type="int", required=False),
        ],
        outputs=[
            TaskIO(name="product", type="int", required=True),
        ],
        usage="flow.yaml では tasks.multiply.use: \"demo/multiply\" として束ねる。",
    )
```

## plug-in の登録

プラグインパッケージの `pyproject.toml` で hook を公開します:

```toml
[project.entry-points."pyoco.tasks"]
custom_demo = "examples.custom_task_demo:register_tasks"
```

同じ環境にインストールすると、pyoco が自動ロードします。

将来 `pyoco-server` に広げる場合も、この package 形が効きます。同じ再利用 task 群を、ローカルのソース断片ではなく wheel として worker へ配りやすくなるからです。

## ワークフローでの使用

`flow.yaml` では登録済み公開名を `use` でローカル名へ束ねます:

```yaml
version: 1

tasks:
  multiply:
    use: "demo/multiply"

flow:
  defaults:
    start: 3
    multiplier: 4
  graph: |
    multiply
```

ローカルで明示上書きしたい場合だけ、`flow.yaml` に `tasks.<name>.callable` を書きます。再利用タスクの基本運用は plug-in 登録です。

## ▶️ 試してみよう

以下のコマンドでフローを実行できます:

```bash
pyoco plugins list
pyoco run --config flow.yaml
```

最終的なコンテキストには以下が含まれます:

```json
{"results": {"multiply": 12}}
```

## まとめ

- **`BaseTask`** を継承し、`run(self, ctx)` を実装します。
- entry point hook で `registry.task_class(...)` を使って登録します。
- `registry.task_info(...)` を併記して、support 情報と plug-in lint を成立させます。
- `flow.yaml` では `tasks.<local_name>.use` で公開名を束ね、`tasks.<name>.callable` はローカル上書き時だけ使います。
- 将来 `pyoco-server` へ広げるなら、package 化した plug-in の方が worker 配布に向いています。

[次へ: 制御と可観測性](08_control_ja.md)
