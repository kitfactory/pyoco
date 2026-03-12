# 2. パラメータと入力

この章では、workflow を「固定デモ」から「入力で振る舞いが変わる道具」へ進めます。例は小さいままですが、考え方はそのまま大きな flow に伸ばせます。

## 🎯 目標
- 設定ファイルからタスクにパラメータを渡す。
- コマンドラインからパラメータを上書きする。

## ✍️ 1. `tasks.py` の更新
引数を受け取るように `tasks.py` を修正します。

```python
from pyoco.dsl.syntax import task

@task
def greet(ctx, name, greeting="Hello"):
    print(f"{greeting}, {name}!")
```

- Pyoco は、関数引数と名前が一致するパラメータを自動的に注入します。

## 🗺️ 2. `flow.yaml` の更新
`flow.yaml` を更新して、デフォルトパラメータを定義します。

```yaml
version: 1

tasks:
  greet:
    callable: "tasks:greet"

flow:
  defaults:
    name: "User"
    greeting: "Hi"
  graph: |
    greet
```

- `defaults`: パラメータのグローバルなデフォルト値を設定します。
- `callable`: この章のような小さな例では十分です。継続利用する flow では plug-in task を `tasks.<local_name>.use` で束ねる方法を優先します。

## ▶️ 3. デフォルト値で実行
前回と同様に実行します。

```bash
pyoco run --config flow.yaml
```

出力:
```
Hi, User!
```

## 🎛️ 4. CLI から上書き
`--param` フラグを使用してパラメータを上書きできます。

```bash
pyoco run --config flow.yaml --param name=Alice --param greeting=Welcome
```

出力:
```
Welcome, Alice!
```

これにより、コードを変更することなく、異なるコンテキストでワークフローを再利用できます。

## 🧠 5. 高度なセレクタ
セレクタを使用して、`flow.yaml` 内でコンテキストパラメータや環境変数に直接アクセスすることもできます。

### コンテキストパラメータ (`$ctx.params`)
$ctx.params を標準にすると、意図しない上書きを避けられます。自動注入に頼る代わりに、パラメータを明示的にマッピングできます。

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

### `$node.<task>.output` を使う場面
同じ `$ctx.params` キーが上書きされる場合や、上流出力を明示したい場合は `$node.<task>.output` を使います。

```yaml
tasks:
  summarize:
    inputs:
      data: "$node.build_report.output"
```

ここまでで、よく使うデフォルト値、1回だけの CLI 上書き、そして明示的な selector の3つが揃いました。小さい workflow でも実務 flow でも、この3つが土台になります。

[次へ: データフローと依存関係](03_data_flow_ja.md)
