# 🐇 Pyoco

**pyoco is a minimal, pure-Python DAG engine for defining and running simple task-based workflows.**

## ✨ Why It Feels Easy

- ⚡ **Try it in minutes**: a tiny local workflow is enough to get your first success.
- 🧩 **Grow without changing tools**: when your flow becomes reusable, move to plug-ins + `tasks.<local>.use`.
- 🪶 **Stay lightweight**: no scheduler cluster, no metadata DB, no “platform first” setup.

Pyoco is intentionally much smaller than full-scale workflow engines like Airflow. It is built for local development, single-machine execution, and “I want to run this now” workflows.

## 🚦 Pick Your Route

- **Fastest first success**: write one tiny task and run it locally. Great for learning or debugging an idea.
- **Recommended project route**: package reusable tasks as entry point plug-ins, then bind them in `flow.yaml` with `tasks.<local_name>.use`.

If you are new to Pyoco, do the quick win first. If you are building something you want to keep, learn the plug-in route right after.

## ✨ Features

- **Pure Python**: No external services or heavy dependencies required.
- **Minimal DAG model**: Tasks and dependencies are defined directly in code.
- **Task-oriented**: Focus on "small workflows" that should be easy to read and maintain.
- **Graph DSL controls**: `>>` pipeline + `node_name: task_ref` + `pipe/switch/repeat/foreach/until` for branching, reuse, and loops in `flow.yaml`.
- **Friendly trace logs**: Runs can be traced step by step from the terminal with cute (or plain) logs.
- **Parallel Execution**: Automatically runs independent tasks in parallel.
- **Artifact Management**: Easily save and manage task outputs and files.
- **Observability**: Track execution with unique Run IDs and detailed state transitions.
- **Control**: Cancel running workflows gracefully with `Ctrl+C`.

## 📦 Installation

```bash
pip install pyoco
```

## 🚀 Quick Win: Run Something in 60 Seconds

This is the **shortest possible hello**. It keeps everything in one file so you can feel the engine immediately.

```python
from pyoco import task
from pyoco.core.models import Flow
from pyoco.core.engine import Engine

@task
def fetch_data(ctx):
    print("🐰 Fetching data...")
    return {"id": 1, "value": "carrot"}

@task
def process_data(ctx, data):
    print(f"🥕 Processing: {data['value']}")
    return data['value'].upper()

@task
def save_result(ctx, result):
    print(f"✨ Saved: {result}")

# Define the flow
flow = Flow(name="hello_pyoco")
flow >> fetch_data >> process_data >> save_result

# Wire inputs (explicitly for this example)
process_data.task.inputs = {"data": "$node.fetch_data.output"}
save_result.task.inputs = {"result": "$node.process_data.output"}

if __name__ == "__main__":
    engine = Engine()
    engine.run(flow)
```

Run it:

```bash
python examples/hello_pyoco.py
```

Output:

```
🐇 pyoco > start flow=hello_pyoco
🏃 start node=fetch_data
🐰 Fetching data...
✅ done node=fetch_data (0.30 ms)
🏃 start node=process_data
🥕 Processing: carrot
✅ done node=process_data (0.23 ms)
🏃 start node=save_result
✨ Saved: CARROT
✅ done node=save_result (0.30 ms)
🥕 done flow=hello_pyoco
```

See [examples/hello_pyoco.py](examples/hello_pyoco.py) for the full code.

## 🧭 Build It the Recommended Way

When a task should be reused, shared, or documented, prefer this shape:

1. Publish a Task subclass from a plug-in package.
2. Give it a stable public name such as `vision/image_classify`.
3. Bind that public name to a local workflow name with `tasks.<local_name>.use`.

That is the model Pyoco now treats as the default for real projects.

## 🧾 flow.yaml Graph DSL

This is the model to learn once you move past a one-file experiment. `flow.yaml` keeps the graph readable, and plug-in task names keep reuse clean.

For production-style task sharing, prefer **entry point plug-ins that register Task subclasses** and bind them in `flow.yaml` via `tasks.<local_name>.use`. Keep `tasks.<name>.callable` as an explicit local override or migration path.

```yaml
version: 1

tasks:
  prepare:
    use: "demo/prepare"
  choose_mode:
    use: "demo/choose_mode"
  run_batch:
    use: "demo/run_batch"
  process_item:
    use: "demo/process_item"
  poll_status:
    use: "demo/poll_status"
  finish:
    use: "demo/finish"

flow:
  defaults:
    mode: "batch"
    items: ["A", "B", "C"]
    done: false
  graph: |
    prepare
    >> choose_mode
    >> switch(on={{mode}}){
      batch: first_batch: run_batch >> second_batch: run_batch;
      default: run_batch;
    }
    >> foreach(over={{items}}, item=it, index=idx){ process_item }
    >> until(cond={{params.done}}, max_iter=5){ poll_status }
    >> finish
```

- `>>`: sequential dependency
- `node_name: task_ref`: reuse one task definition with a distinct runtime node name
- `tasks.<local_name>.use`: bind a registered public task name such as `demo/run_batch` to a local graph name
- `pipe(NAME)`: inline expansion from top-level `pipes`
- `switch(on=...){ ... }`: single-branch selection
- `repeat` / `foreach` / `until`: control loops

Want a gentle walkthrough instead of reading specs? Start with [docs/tutorial/index.md](docs/tutorial/index.md).

## 🏗️ Architecture

Pyoco is designed with a simple flow:

```
+-----------+        +------------------+        +-----------------+
| User Code |  --->  | pyoco.core.Flow  |  --->  | trace/logger    |
| (Tasks)   |        | (Engine)         |        | (Console/File)  |
+-----------+        +------------------+        +-----------------+
```

1. **User Code**: You define tasks and workflows using Python decorators.
2. **Core Engine**: The engine resolves dependencies and executes tasks (in parallel where possible).
3. **Trace**: Execution events are sent to the trace backend for logging (cute or plain).

## 🎭 Modes

Pyoco has two output modes:

- **Cute Mode** (Default): Uses emojis and friendly messages. Best for local development and learning.
- **Non-Cute Mode**: Plain text logs. Best for CI/CD and production monitoring.

You can switch modes using an environment variable:

```bash
export PYOCO_CUTE=0  # Disable cute mode
```

Or via CLI flag:

```bash
pyoco run --non-cute ...
```

## 🔭 Observability / Server (Archived)

Observability and server-related docs are archived and out of scope for the current requirements.  
See `docs/archive/observability.md` and `docs/archive/roadmap.md`.

## 🌐 Distributed Execution with `pyoco-server`

`pyoco` focuses on local/single-machine workflow execution.  
For distributed workers, queueing, and remote run management, use **`pyoco-server`**.

- The practical win of the plug-in model is distribution: packaged task sets can travel as wheels instead of ad-hoc source copies.
- `pyoco-server` provides the worker/server side for that model, so reusable task packages fit naturally when you want to fan out execution beyond one machine.
- Repository: <https://github.com/kitfactory/pyoco-server>
- Detailed setup, operations, and compatibility are documented in `pyoco-server`.

## 🧩 Plug-ins

Need to share domain-specific tasks? Publish an entry point under `pyoco.tasks` and pyoco will auto-load it. This is the **default recommended path**. Register **Task subclasses first** (callables still work with warnings), give them stable public names like `vision/image_classify`, then bind them with `tasks.<local_name>.use` in `flow.yaml`. See [docs/plugins.md](docs/plugins.md) for examples, quickstart, and `pyoco plugins list` / `pyoco plugins lint`.

Another reason this path matters: once tasks live in a package, they are much easier to distribute to `pyoco-server` workers as versioned plug-ins.

**Big data note:** pass handles, not copies. For large tensors/images, stash paths or handles in `ctx.artifacts`/`ctx.scratch` and let downstream tasks materialize only when needed. For lazy pipelines (e.g., DataPipe), log the pipeline when you actually iterate (typically the training task) instead of materializing upstream.

## 🧭 Task Discovery (Security)

Pyoco does not allow configuring discovery scope in `flow.yaml` (the `discovery:` key is rejected) to reduce the risk of importing unexpected code.

- **Entry point plug-ins**: auto-loaded from `importlib.metadata.entry_points(group="pyoco.tasks")`
- **Extra imports (ops-controlled)**: set `PYOCO_DISCOVERY_MODULES` (comma/space-separated module names), e.g. `PYOCO_DISCOVERY_MODULES=tasks,myapp.extra_tasks`
- **Flow-local bindings**: prefer `tasks.<local_name>.use: "namespace/task_name"` for registered plug-in tasks
- **Explicit callables**: keep `tasks.<name>.callable` for local overrides or small ad-hoc flows

## 📚 Documentation

- [Tutorials](docs/tutorial/index.md)
- [Roadmap (Archived)](docs/archive/roadmap.md)

## 💖 Contributing

We love contributions! Please feel free to submit a Pull Request.

---

*Made with 🥕 by the Pyoco Team.*
