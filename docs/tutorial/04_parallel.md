# 4. Control Components (pipe / switch / repeat / foreach / until)

In this chapter, you will learn the control components of the current graph DSL.

## Goal
- Reuse pipeline fragments with `pipe(NAME)`.
- Select one branch with `switch(on=...){ ... }`.
- Run repeated logic with `repeat` / `foreach` / `until`.

## 1. Define Tasks (`tasks.py`)

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

## 2. Configure Flow (`flow.yaml`)

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

- `pipe(setup)`: expands `pipes.setup` and connects it in-place.
- `switch(on={{mode}}){ ... }`: runs one matching branch.
- `repeat(count=2){ ... }`: runs the body a fixed number of times.
- `foreach(over={{items}}, item=it, index=idx){ ... }`: iterates list items with aliases.
- `until(cond={{params.done}}, max_iter=5){ ... }`: repeats until condition becomes true.

## 3. Check and Run

```bash
pyoco check --config flow.yaml --dry-run
pyoco run --config flow.yaml
```

[Next: Artifacts & Saving](05_artifacts.md)
