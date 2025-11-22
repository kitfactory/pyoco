# 3. データフローと依存関係

この章では、タスク同士を接続し、データをやり取りする方法を学びます。

## 目標
- タスク間の依存関係を定義する (`A >> B`)。
- あるタスクの出力を別のタスクの入力として渡す。

## 1. タスクの定義 (`tasks.py`)
数値を生成し、それを倍にし、フォーマットするパイプラインを作成します。

```python
from pyoco.dsl.syntax import task
import random

@task
def generate_number(ctx):
    num = random.randint(1, 10)
    print(f"Generated: {num}")
    return num

@task
def multiply(ctx, value):
    result = value * 2
    print(f"Multiplied: {result}")
    return result

@task
def format_result(ctx, number):
    message = f"The final result is: {number}"
    print(message)
    return message
```

## 2. フローの設定 (`flow.yaml`)
依存関係を定義し、入力をマッピングする必要があります。

```yaml
version: 1

discovery:
  glob_modules:
    - "tasks.py"

tasks:
  multiply:
    inputs:
      # 'generate_number' の出力を 'value' 引数として使用
      value: "$node.generate_number.output"
  format_result:
    inputs:
      # 'multiply' の出力を 'number' 引数として使用
      number: "$node.multiply.output"

flows:
  main:
    graph: |
      generate_number >> multiply >> format_result
```

- `>>`: 実行順序を定義します。`generate_number` が最初に実行され、次に `multiply`、最後に `format_result` が実行されます。
- `$node.<TaskName>.output`: 前のタスクの戻り値にアクセスするためのセレクタです。

## 3. 実行
```bash
pyoco run --config flow.yaml
```

出力:
```
Generated: 5
Multiplied: 10
The final result is: 10
```

[次へ: 並列処理と分岐](04_parallel_ja.md)
