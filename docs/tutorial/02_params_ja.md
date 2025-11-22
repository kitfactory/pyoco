# 2. パラメータと入力

この章では、パラメータと入力を使用してタスクを動的にする方法を学びます。

## 目標
- 設定ファイルからタスクにパラメータを渡す。
- コマンドラインからパラメータを上書きする。

## 1. `tasks.py` の更新
引数を受け取るように `tasks.py` を修正します。

```python
from pyoco.dsl.syntax import task

@task
def greet(ctx, name, greeting="Hello"):
    print(f"{greeting}, {name}!")
```

- Pyoco は、関数引数と名前が一致するパラメータを自動的に注入します。

## 2. `flow.yaml` の更新
`flow.yaml` を更新して、デフォルトパラメータを定義します。

```yaml
version: 1

discovery:
  glob_modules:
    - "tasks.py"

flows:
  main:
    defaults:
      name: "User"
      greeting: "Hi"
    graph: |
      greet
```

- `defaults`: パラメータのグローバルなデフォルト値を設定します。

## 3. デフォルト値で実行
前回と同様に実行します。

```bash
pyoco run --config flow.yaml
```

出力:
```
Hi, User!
```

## 4. CLI から上書き
`--param` フラグを使用してパラメータを上書きできます。

```bash
pyoco run --config flow.yaml --param name=Alice --param greeting=Welcome
```

出力:
```
Welcome, Alice!
```

これにより、コードを変更することなく、異なるコンテキストでワークフローを再利用できます。

## 5. 高度なセレクタ
セレクタを使用して、`flow.yaml` 内でコンテキストパラメータや環境変数に直接アクセスすることもできます。

### コンテキストパラメータ (`$ctx.params`)
自動注入に頼る代わりに、パラメータを明示的にマッピングできます。

```yaml
tasks:
  greet:
    inputs:
      name: "$ctx.params.name"
```

### 環境変数 (`$env`)
`$env` を使用して環境変数にアクセスできます。

```yaml
tasks:
  api_call:
    inputs:
      api_key: "$env.API_KEY"
```

[次へ: データフローと依存関係](03_data_flow_ja.md)
