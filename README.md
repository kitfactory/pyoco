# 🐇 Pyoco

**pyoco is a minimal, pure-Python DAG engine for defining and running simple task-based workflows.**

## Overview

Pyoco is designed to be significantly smaller, lighter, and have fewer dependencies than full-scale workflow engines like Airflow. It is optimized for local development and single-machine execution.

You can define tasks and their dependencies entirely in Python code using decorators and a simple API. There is no need for complex configuration files or external databases.

It is ideal for small jobs, development environments, and personal projects where a full-stack workflow engine would be overkill.

## ✨ Features

- **Pure Python**: No external services or heavy dependencies required.
- **Minimal DAG model**: Tasks and dependencies are defined directly in code.
- **Task-oriented**: Focus on "small workflows" that should be easy to read and maintain.
- **Friendly trace logs**: Runs can be traced step by step from the terminal with cute (or plain) logs.
- **Parallel Execution**: Automatically runs independent tasks in parallel.
- **Artifact Management**: Easily save and manage task outputs and files.
- **Observability**: Track execution with unique Run IDs and detailed state transitions.
- **Control**: Cancel running workflows gracefully with `Ctrl+C`.

## 📦 Installation

```bash
pip install pyoco
```

## 🚀 Usage

Here is a minimal example of a pure-Python workflow.

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

## 🏗️ Architecture

Pyoco is designed with a simple flow:

```
+-----------+        +------------------+        +-----------------+
| User Code |  --->  | pyoco.core.Flow  |  --->  | trace/logger    |
| (Tasks)   |        | (Engine)         |        | (Console/File)  |
+-----------+        +------------------+        +-----------------+
```

1. **User Code**: You define tasks and flows using Python decorators.
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

## 🔭 Observability Bridge (v0.5)

- `/metrics` exposes Prometheus counters (`pyoco_runs_total`, `pyoco_runs_in_progress`) and histograms (`pyoco_task_duration_seconds`, `pyoco_run_duration_seconds`). Point Grafana/Prometheus at it to watch pipelines without opening sockets.
- `/runs` now accepts `status`, `flow`, `limit` query params; `/runs/{id}/logs?tail=100` fetches only the latest snippets for dashboards.
- Webhook notifications fire when runs COMPLETE/FAIL—configure via `PYOCO_WEBHOOK_*` env vars and forward to Slack or your alerting stack.
- Import `docs/grafana_pyoco_cute.json` for a lavender/orange starter dashboard (3 panels: in-progress count, completion trend, per-flow latency).
- 詳細な手順は [docs/observability.md](docs/observability.md) を参照してください。

## 🧩 Plug-ins

Need to share domain-specific tasks? Publish an entry point under `pyoco.tasks` and pyoco will auto-load it. In v0.5.1 we recommend **Task subclasses first** (callables still work with warnings). See [docs/plugins.md](docs/plugins.md) for examples, quickstart, and `pyoco plugins list` / `pyoco plugins lint`.

**Big data note:** pass handles, not copies. For large tensors/images, stash paths or handles in `ctx.artifacts`/`ctx.scratch` and let downstream tasks materialize only when needed. For lazy pipelines (e.g., DataPipe), log the pipeline when you actually iterate (typically the training task) instead of materializing upstream.

## 📚 Documentation

- [Tutorials](docs/tutorial/index.md)
- [Roadmap](docs/roadmap.md)

## 💖 Contributing

We love contributions! Please feel free to submit a Pull Request.

---

*Made with 🥕 by the Pyoco Team.*
