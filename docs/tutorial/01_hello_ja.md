# 1. Hello World

この章は **最短で最初の成功体験を得るための章** です。まずは local の `callable` 束ねで、Pyoco がどう動くかをすぐ試します。

継続利用する形を先に知りたい場合は、この章のあとに [7章](07_custom_tasks_ja.md) へ進んでください。

## 🎯 目標
- "Hello, Pyoco!" と出力するシンプルなタスクを作成する。
- ワークフロー設定を定義する。
- CLI を使ってワークフローを実行する。

## 🧱 1. プロジェクト構成
新しいディレクトリ（例: `my_first_flow`）を作成し、以下の2つのファイルを用意します。
- `tasks.py`: Pythonコードを記述します。
- `flow.yaml`: ワークフローの構造を定義します。

## ✍️ 2. タスクの定義 (`tasks.py`)
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

## 🗺️ 3. フローの設定 (`flow.yaml`)
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

- `tasks`: この章では簡潔さのために task 名と Python callable を対応付けています。再利用前提のプロジェクトでは、登録済み plug-in task を `tasks.<local_name>.use` で束ねる方法を優先してください。
- `flow`: 単一フローを定義します。
- `graph`: 実行するタスクを記述します。ここではシンプルに `hello` だけです。

## ▶️ 4. 実行！
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

次に「再利用できる形」を見たい場合は、[BaseTask を使ったカスタムタスク](07_custom_tasks_ja.md) が推奨ルートです。

[次へ: パラメータと入力](02_params_ja.md)
