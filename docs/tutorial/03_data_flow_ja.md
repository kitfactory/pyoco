# 3. データフローと依存関係

この章では、別々の task が「ひとつの workflow」として見えてくるところまで進みます。出力を下流入力へつなぎ、graph が単なる関数列ではなく流れとして読めるようにします。

## 🎯 目標
- タスク間の依存関係を定義する (`A >> B`)。
- あるタスクの出力を別のタスクの入力として渡す。

## ✍️ 1. タスクの定義 (`tasks.py`)
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

## 🗺️ 2. フローの設定 (`flow.yaml`)
依存関係を定義し、入力をマッピングする必要があります。基本は `$ctx.params` でつなぎます。

```yaml
version: 1

tasks:
  generate_number:
    callable: "tasks:generate_number"
    outputs:
      - "params.generated"
  multiply:
    callable: "tasks:multiply"
    inputs:
      # $ctx.params で連携するのが標準
      value: "$ctx.params.generated"
    outputs:
      - "params.multiplied"
  format_result:
    callable: "tasks:format_result"
    inputs:
      # $ctx.params で連携するのが標準
      number: "$ctx.params.multiplied"
    outputs:
      - "params.formatted"

flow:
  graph: |
    generate_number >> multiply >> format_result
```

- `>>`: 実行順序を定義します。`generate_number` が最初に実行され、次に `multiply`、最後に `format_result` が実行されます。
- `$ctx.params.<key>`: 共有パラメータでタスクをつなぐ標準的な方法です。
- `$node.<TaskName>.output`: 共有パラメータの上書き回避や、上流出力を明示したい場合に使います。
- この章も簡潔さを優先して local `callable` を使っています。再利用する task になったら、同じ考え方を plug-in + `tasks.<local>.use` へ移します。

## ▶️ 3. 実行
```bash
pyoco run --config flow.yaml
```

出力:
```
Generated: 5
Multiplied: 10
The final result is: 10
```

2章で「入力で変わる flow」を作り、この章で「つながる flow」になりました。次は分岐や反復を加えても読みやすさを保つ方法へ進みます。

[次へ: 制御コンポーネント (pipe/switch/repeat/foreach/until)](04_parallel_ja.md)
