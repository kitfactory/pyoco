# 4. 並列処理と分岐

この章では、タスクを並列に実行する方法と、分岐ロジックを扱う方法を学びます。

## 目標
- `&` を使用して独立したタスクを同時実行する。
- `|` を使用して分岐ロジックを定義する。

## 1. 並列実行
歯磨きと洗顔を同時に行う（マルチタスクが得意なら！）朝のルーチンをシミュレートしてみましょう。

### `tasks.py`
```python
from pyoco.dsl.syntax import task
import time

@task
def brush_teeth(ctx):
    print("Brushing teeth...")
    time.sleep(1)
    return "teeth clean"

@task
def wash_face(ctx):
    print("Washing face...")
    time.sleep(1)
    return "face clean"

@task
def breakfast(ctx):
    print("Eating breakfast...")
    return "full"
```

### `flow.yaml`
```yaml
version: 1
discovery:
  glob_modules: ["tasks.py"]

flows:
  morning:
    graph: |
      (brush_teeth & wash_face) >> breakfast
```

- `(A & B)`: 並列グループを定義します。両方のタスクが同時に開始されます。
- `>> C`: タスク C は、A と B の **両方** が完了するのを待ちます。

## 2. 分岐 (OR-Join)
場合によっては、前のタスクのいずれか1つが成功すれば次に進みたいことがあります。

```yaml
flows:
  flexible_morning:
    graph: |
      (brush_teeth | wash_face) >> breakfast
```

- `(A | B)`: 分岐を定義します。
- `>> C`: タスク C は、A または B の **いずれか** が完了するのを待ちます。これは「早い者勝ち」やオプションパスのシナリオで役立ちます。

## 3. 実行
並列フローを実行します。
```bash
pyoco run --config flow.yaml --flow morning --cute
```

かわいいトレース出力で、タスクが一緒に実行されているのが確認できるはずです！

[次へ: アーティファクトと保存](05_artifacts_ja.md)
