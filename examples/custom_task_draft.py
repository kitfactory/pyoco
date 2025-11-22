from pyoco.core.models import Task
from pyoco.dsl.syntax import TaskWrapper

class CustomTask(Task):
    def __init__(self, name: str, **kwargs):
        super().__init__(func=self.run, name=name, **kwargs)

    def run(self, ctx, **kwargs):
        raise NotImplementedError("Subclasses must implement run()")

# Usage example
class MyTask(CustomTask):
    def run(self, ctx, **kwargs):
        print(f"Running {self.name}")
        return "done"

# How to register?
# The DSL expects TaskWrapper or Task.
# We can instantiate MyTask and wrap it?
# Or just use it directly if TaskLoader supports it.
