# 7. Custom Tasks with BaseTask

In this chapter we show how to create reusable, structured tasks by subclassing the library‑provided abstract base class **`BaseTask`** and decorating the implementation method with ``@task``.

## Why use `BaseTask`?
- Gives a clear contract (`run(self, ctx)`) for all custom tasks.
- Allows you to share helper methods or state between multiple tasks via inheritance.
- Improves discoverability in the documentation – users know there is a common base class.

## Example implementation
Create a Python module, e.g. `examples/custom_task_demo.py`:

```python
# examples/custom_task_demo.py
from pyoco.core.base_task import BaseTask
from pyoco.dsl.syntax import task

class MultiplyTask(BaseTask):
    """A simple task that multiplies an input value by a factor.

    The ``run`` method receives the execution ``ctx`` which provides access to
    ``inputs`` (populated from ``flow.yaml``) and ``scratch`` where we can store
    intermediate results.
    """

    @task
    def run(self, ctx):
        # ``ctx.inputs`` contains the values defined under ``inputs`` in flow.yaml
        value = ctx.inputs.get("value", 1)
        factor = ctx.inputs.get("factor", 2)
        result = value * factor
        return result
```

## Using the task in a workflow
Add the task to your ``flow.yaml``:

```yaml
version: 1

discovery:
  glob_modules: ["examples/custom_task_demo.py"]

tasks:
  multiply:
    callable: "examples.custom_task_demo:MultiplyTask.run"
    inputs:
      value: "$ctx.params.start"
      factor: "$ctx.params.multiplier"
    outputs:
      - "scratch.product"

flows:
  main:
    graph: |
      multiply
```

When the flow runs, the return value of ``MultiplyTask.run`` will be stored in
``ctx.scratch.product`` and can be accessed by downstream tasks via the selector
``$ctx.scratch.product``.

## Test it yourself
You can run the flow with:

```bash
python -m pyoco run flow.yaml --params.start=3 --params.multiplier=4
```
The final context will contain:

```json
{"scratch": {"product": 12}}
```

## Summary
- Subclass **`BaseTask`** and implement ``run(self, ctx)``.
- Decorate ``run`` with ``@task`` so the DSL recognises it.
- Configure ``inputs`` and ``outputs`` in ``flow.yaml`` just like any other task.
- This pattern encourages reusable, well‑documented task implementations.

[Next: Advanced: Error Handling](06_errors.md)
