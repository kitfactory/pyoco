# 7. Custom Tasks with BaseTask

This is the chapter where Pyoco shifts from “nice demo” to “project you actually want to keep.” The recommended path for reusable tasks is: subclass **`BaseTask`**, publish it as a **plug-in entry point**, then bind the public task name in `flow.yaml`.

## When should you read this chapter?

- 🧩 You want to reuse the same task across multiple flows.
- 📦 You want a package to expose tasks cleanly to other users.
- 🧭 You want `flow.yaml` to stay readable with `tasks.<local>.use`.
- 🌐 You may later run the same task package on `pyoco-server` workers.

## Why use `BaseTask`?
- Gives a clear contract (`run(self, ctx)`) for all custom tasks.
- Allows you to share helper methods or state between multiple tasks via inheritance.
- Improves discoverability in the documentation – users know there is a common base class.

## Example implementation
Create a Python module, e.g. `examples/custom_task_demo.py`:

```python
# examples/custom_task_demo.py
from pyoco.core.base_task import BaseTask
from pyoco.core.models import TaskIO

class MultiplyTask(BaseTask):
    """A simple task that multiplies an input value by a factor.

    The ``run`` method receives the execution ``ctx`` which provides access to
    ``params`` / ``scratch`` and any values resolved from ``flow.yaml``.
    """

    def run(self, ctx):
        value = ctx.params.get("start", 1)
        factor = ctx.params.get("multiplier", 2)
        result = value * factor
        return result


def register_tasks(registry):
    registry.task_class(MultiplyTask, name="demo/multiply")
    registry.task_info(
        name="demo/multiply",
        summary="Multiply an input value by a factor.",
        inputs=[
            TaskIO(name="start", type="int", required=False),
            TaskIO(name="multiplier", type="int", required=False),
        ],
        outputs=[
            TaskIO(name="product", type="int", required=True),
        ],
        usage="Bind from flow.yaml with tasks.multiply.use: \"demo/multiply\".",
    )
```

## Register the plug-in
Expose the hook in your plug-in package's `pyproject.toml`:

```toml
[project.entry-points."pyoco.tasks"]
custom_demo = "examples.custom_task_demo:register_tasks"
```

After installing the package into the same environment, pyoco auto-loads it.

If you later move to `pyoco-server`, this package shape becomes even more useful: the same reusable task set can be distributed as a wheel to workers instead of being copied around as local source.

## Using the task in a workflow
Bind the registered public name from `flow.yaml`:

```yaml
version: 1

tasks:
  multiply:
    use: "demo/multiply"

flow:
  defaults:
    start: 3
    multiplier: 4
  graph: |
    multiply
```

If you need an explicit local override, you can still define `tasks.<name>.callable` in `flow.yaml`, but the default recommendation is to keep reusable tasks in plug-ins.

## ▶️ Test it yourself
You can run the flow with:

```bash
pyoco plugins list
pyoco run --config flow.yaml
```

The final context will contain:

```json
{"results": {"multiply": 12}}
```

## Summary
- Subclass **`BaseTask`** and implement ``run(self, ctx)``.
- Register the task with `registry.task_class(...)` in an entry point hook.
- Pair it with `registry.task_info(...)` so support info and plug-in lint stay useful.
- Bind the public task name with `tasks.<local_name>.use`; keep `tasks.<name>.callable` for local overrides only.
- If the workflow later moves to `pyoco-server`, packaged plug-ins are much easier to distribute to workers.

[Next: Advanced: Error Handling](06_errors.md)
