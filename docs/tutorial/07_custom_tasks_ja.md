# 7. BaseTask を使ったカスタムタスク

この章では、ライブラリが提供する抽象基底クラス **`BaseTask`** を継承し、`@task` デコレータを使用することで、再利用可能で構造化されたタスクを作成する方法を学びます。

## なぜ `BaseTask` を使うのか？

- すべてのカスタムタスクに対して明確な契約 (`run(self, ctx)`) を与えます。
- 継承を通じて、複数のタスク間でヘルパーメソッドや状態を共有できます。
- ドキュメントの発見性が向上します（ユーザーは共通の基底クラスがあることを知ることができます）。

## 実装例

Python モジュールを作成します（例: `examples/custom_task_demo.py`）:

```python
# examples/custom_task_demo.py
from pyoco.core.base_task import BaseTask
from pyoco.dsl.syntax import task

class MultiplyTask(BaseTask):
    """入力値を係数で掛け合わせるシンプルなタスク。

    ``run`` メソッドは実行コンテキスト ``ctx`` を受け取ります。
    これにより、``flow.yaml`` から入力された ``inputs`` や、
    中間結果を保存するための ``scratch`` にアクセスできます。
    """

    @task
    def run(self, ctx):
        # ``ctx.inputs`` には flow.yaml の ``inputs`` で定義された値が含まれます
        value = ctx.inputs.get("value", 1)
        factor = ctx.inputs.get("factor", 2)
        result = value * factor
        return result
```

## ワークフローでの使用

`flow.yaml` にタスクを追加します:

```yaml
version: 1

discovery:
  glob_modules: ["examples/custom_task_demo.py"]

tasks:
  multiply:
    callable: "examples.custom_task_demo:MultiplyTask.run"
    inputs:
      value: "$ctx.params.start"
      factor: "$ctx.params.multiplier"
    outputs:
      - "scratch.product"

flows:
  main:
    graph: |
      multiply
```

フローが実行されると、`MultiplyTask.run` の戻り値が `ctx.scratch.product` に保存され、下流のタスクからセレクタ `$ctx.scratch.product` を介してアクセスできるようになります。

## 試してみよう

以下のコマンドでフローを実行できます:

```bash
python -m pyoco run flow.yaml --params.start=3 --params.multiplier=4
```

最終的なコンテキストには以下が含まれます:

```json
{"scratch": {"product": 12}}
```

## まとめ

- **`BaseTask`** を継承し、`run(self, ctx)` を実装します。
- DSL が認識できるように `run` を `@task` でデコレートします。
- 他のタスクと同様に、`flow.yaml` で `inputs` と `outputs` を設定します。
- このパターンは、再利用可能でドキュメント化されたタスクの実装を推奨します。

[次へ: 制御と可観測性](08_control_ja.md)
