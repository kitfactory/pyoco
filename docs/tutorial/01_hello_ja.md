# 1. Hello World

この章では、最初の Pyoco ワークフローを作成して実行します。

## 目標
- "Hello, Pyoco!" と出力するシンプルなタスクを作成する。
- ワークフロー設定を定義する。
- CLI を使ってワークフローを実行する。

## 1. プロジェクト構成
新しいディレクトリ（例: `my_first_flow`）を作成し、以下の2つのファイルを用意します。
- `tasks.py`: Pythonコードを記述します。
- `flow.yaml`: ワークフローの構造を定義します。

## 2. タスクの定義 (`tasks.py`)
`tasks.py` を開き、以下のコードを追加します。

```python
from pyoco.dsl.syntax import task

@task
def hello(ctx):
    print("Hello, Pyoco!")
    return "done"
```

- `@task` デコレータは、関数を Pyoco タスクとしてマークします。
- `ctx` 引数はコンテキストオブジェクトで、パラメータやその他の機能にアクセスするために使用します（後の章で使用します）。

## 3. フローの設定 (`flow.yaml`)
`flow.yaml` を開き、ワークフローを定義します。

```yaml
version: 1

tasks:
  hello:
    callable: "tasks:hello"

# フローの定義
flow:
  graph: |
    hello
```

- `tasks`: タスク名と Python callable を対応付けます。
- `flow`: 単一フローを定義します。
- `graph`: 実行するタスクを記述します。ここではシンプルに `hello` だけです。

## 4. 実行！
ターミナルを開き、以下のコマンドを実行します。

```bash
pyoco run --config flow.yaml
```

以下のような出力が表示されるはずです。

```
🐇 pyoco > start flow=main
🏃 start node=hello
Hello, Pyoco!
✅ done node=hello (0.05 ms)
🥕 done flow=main
```

おめでとうございます！最初の Pyoco ワークフローを実行できました。

[次へ: パラメータと入力](02_params_ja.md)
