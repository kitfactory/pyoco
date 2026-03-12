# 5. Artifacts & Outputs

This chapter is about leaving useful traces behind. A workflow becomes more valuable when its results can be reused, inspected, or handed to the next step.

## 🎯 Goal
- Save task results to the Context using `outputs`.
- Save files (artifacts) manually using `ctx.save_artifact`.

## 📦 1. Saving to Context (`outputs`)
You can configure Pyoco to save a task's return value to specific paths in the Context. This is useful for passing data to other tasks without direct dependency wiring.

### `tasks.py`
```python
from pyoco.dsl.syntax import task

@task
def calculate_metrics(ctx):
    return {"accuracy": 0.95, "loss": 0.05}
```

### `flow.yaml`
```yaml
version: 1

tasks:
  calculate_metrics:
    callable: "tasks:calculate_metrics"
    outputs:
      # Save return value to ctx.scratch.metrics
      - "scratch.metrics"

flow:
  graph: |
    calculate_metrics
```

Later tasks can access this data via `$ctx.scratch.metrics`.

## 🗂️ 2. Saving Artifacts (Files)
To save files (like reports, images, or models), use `ctx.save_artifact` within your task code.

```python
@task
def generate_chart(ctx):
    data = "Chart Data..."
    # Save to artifacts/charts/my_chart.txt
    path = ctx.save_artifact("charts/my_chart.txt", data)
    print(f"Saved chart to {path}")
```

This keeps your configuration clean (`inputs` for data sources, `outputs` for data destinations) while leaving file persistence logic in Python.

Use `outputs` when the next task needs structured values. Use artifacts when you want durable files people or other tools can inspect later.

[Next: Advanced: Error Handling](06_errors.md)
