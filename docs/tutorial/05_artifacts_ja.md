# 5. アーティファクトと出力

この章では、タスクの出力を管理し、データを永続化する方法を学びます。

## 目標
- `outputs` を使用してタスクの結果をコンテキストに保存する。
- `ctx.save_artifact` を使用してファイル（アーティファクト）を手動で保存する。

## 1. コンテキストへの保存 (`outputs`)
Pyoco を設定して、タスクの戻り値をコンテキストの特定のパスに保存できます。これは、直接的な依存関係を結ばずに他のタスクにデータを渡す場合に便利です。

### `tasks.py`
```python
from pyoco.dsl.syntax import task

@task
def calculate_metrics(ctx):
    return {"accuracy": 0.95, "loss": 0.05}
```

### `flow.yaml`
```yaml
version: 1
discovery:
  glob_modules: ["tasks.py"]

tasks:
  calculate_metrics:
    outputs:
      # 戻り値を ctx.scratch.metrics に保存
      - "scratch.metrics"

flows:
  main:
    graph: |
      calculate_metrics
```

後続のタスクは `$ctx.scratch.metrics` を介してこのデータにアクセスできます。

## 2. アーティファクト（ファイル）の保存
ファイル（レポート、画像、モデルなど）を保存するには、タスクコード内で `ctx.save_artifact` を使用します。

```python
@task
def generate_chart(ctx):
    data = "Chart Data..."
    # artifacts/charts/my_chart.txt に保存
    path = ctx.save_artifact("charts/my_chart.txt", data)
    print(f"Saved chart to {path}")
```

これにより、設定ファイルはクリーンに保たれ（`inputs` はデータソース、`outputs` はデータの行き先）、ファイルの永続化ロジックは Python コード内に記述されます。

[次へ: 応用: エラーハンドリング](06_errors_ja.md)
