# 4. 制御コンポーネント (pipe / switch / repeat / foreach / until)

この章では、graph DSL が「便利だ」と感じ始めるところまで進みます。基本の `>>` はそのままに、分岐・再利用・反復を足していきます。

## 🎯 目標
- `pipe(NAME)` でパイプ断片を再利用する。
- `switch(on=...){ ... }` で1つの分岐を選択する。
- `repeat` / `foreach` / `until` で反復処理を定義する。

## ✍️ 1. タスクの定義 (`tasks.py`)

```python
from pyoco.dsl.syntax import task

@task
def prepare(ctx):
    print("prepare")
    return "ok"

@task
def choose_mode(ctx):
    return ctx.params.get("mode", "batch")

@task
def run_batch(ctx):
    count = ctx.params.get("batch_count", 0) + 1
    ctx.params["batch_count"] = count
    print(f"batch run: {count}")
    return count

@task
def process_item(ctx):
    item = ctx.get_var("it")
    index = ctx.get_var("idx")
    line = f"{index}:{item}"
    ctx.params.setdefault("processed", []).append(line)
    print(f"item: {line}")
    return line

@task
def poll_status(ctx):
    polls = ctx.params.get("polls", 0) + 1
    ctx.params["polls"] = polls
    if polls >= 2:
        ctx.params["done"] = True
    print(f"poll: {polls}")
    return polls

@task
def finish(ctx):
    print("finish")
    return {
        "batch_count": ctx.params.get("batch_count", 0),
        "processed": ctx.params.get("processed", []),
        "polls": ctx.params.get("polls", 0),
    }
```

## 🗺️ 2. フロー設定 (`flow.yaml`)

```yaml
version: 1

pipes:
  setup: "prepare >> choose_mode"

tasks:
  prepare:
    callable: "tasks:prepare"
  choose_mode:
    callable: "tasks:choose_mode"
  run_batch:
    callable: "tasks:run_batch"
  process_item:
    callable: "tasks:process_item"
  poll_status:
    callable: "tasks:poll_status"
  finish:
    callable: "tasks:finish"
    outputs:
      - "params.summary"

flow:
  defaults:
    mode: "batch"
    items: ["A", "B", "C"]
    done: false
  graph: |
    pipe(setup)
    >> switch(on={{mode}}){
      batch: repeat(count=2){ run_batch };
      default: run_batch;
    }
    >> foreach(over={{items}}, item=it, index=idx){ process_item }
    >> until(cond={{params.done}}, max_iter=5){ poll_status }
    >> finish
```

- `pipe(setup)`: `pipes.setup` をその場で展開して接続します。
- `switch(on={{mode}}){ ... }`: 一致した分岐を1つだけ実行します。
- `repeat(count=2){ ... }`: 本文を固定回数だけ実行します。
- `foreach(over={{items}}, item=it, index=idx){ ... }`: リスト要素をエイリアス付きで反復します。
- `until(cond={{params.done}}, max_iter=5){ ... }`: 条件が真になるまで反復します。
- チュートリアルでは local `callable` で短く保っています。実際の project では、同じ graph を plug-in task 名とローカル alias で管理すると読みやすくなります。

## ▶️ 3. チェックと実行

```bash
pyoco check --config flow.yaml --dry-run
pyoco run --config flow.yaml
```

ここまで来ると、flow は小さいままでも制御ロジックは十分に実用的です。次は結果やファイルをどう残すかに進みます。

[次へ: アーティファクトと保存](05_artifacts_ja.md)
