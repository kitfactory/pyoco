# Sample Plug-in: Lazy Data Pipeline Task

This miniature plug-in shows how to register a `Task` subclass that builds a lazy pipeline (e.g., torch DataPipe) and logs its structure only when executed downstream.

```python
# src/pyoco_lazy/entrypoint.py
from pyoco.core.models import Task

class BuildPipe(Task):
    def __init__(self):
        super().__init__(func=self.run, name="build_pipe")
        self.pipeline_steps = []

    def run(self, ctx):
        pipe = ctx.params["pipe"]  # e.g., an existing DataPipe
        # Append lazy transforms; no materialization here
        self.pipeline_steps.extend(["B:resize", "C:augment"])
        return pipe.map(lambda x: x)  # placeholder transform


class Train(Task):
    def __init__(self):
        super().__init__(func=self.run, name="train")

    def run(self, ctx, pipe):
        # At execution time, log the pipeline we inherited
        steps = getattr(pipe, "pipeline_steps", ["(unknown)"])
        print("[pipeline]", " -> ".join(steps + ["G:train"]))
        for batch in pipe:
            # training loop...
            pass
        return "ok"


def register_tasks(registry):
    registry.task_class(BuildPipe)
    registry.task_class(Train)
```

Key points:
- The pipeline is **lazy**; heavy work happens only in `Train`.
- We stash a list of steps and log it when the pipeline is actually iterated.
- No special framework dependency is required; replace the placeholder with your DataPipe.
