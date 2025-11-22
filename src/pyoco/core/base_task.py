# pyoco core - base task abstraction
"""Common abstract base class for user‑defined tasks.

The library already allows registering a plain function with the ``@task``
decorator.  For more structured or reusable implementations you can
subclass :class:`BaseTask` and implement the ``run`` method.  The ``run``
method receives the current :class:`~pyoco.core.context.Context` instance
so you can read inputs, write outputs, or use any other context helpers.

Typical usage::

    from pyoco.core.base_task import BaseTask
    from pyoco.dsl.syntax import task

    class MyTask(BaseTask):
        @task
        def run(self, ctx):
            # ``ctx`` gives access to ``inputs`` and ``scratch`` etc.
            data = ctx.inputs.get("my_input")
            result = data * 2
            return result

In ``flow.yaml`` you reference the method as usual::

    tasks:
      double:
        callable: "my_module:MyTask.run"
        inputs:
          my_input: "$ctx.params.value"
        outputs:
          - "scratch.doubled"

The abstract base class does not enforce any particular input/output
schema – it simply provides a clear contract for developers and makes the
library documentation more discoverable.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseTask(ABC):
    """Abstract base class for custom tasks.

    Subclass this class and implement :meth:`run`.  The method must accept
    a single ``ctx`` argument (the :class:`~pyoco.core.context.Context`
    instance) and return a value that will be stored according to the
    ``outputs`` configuration in ``flow.yaml``.
    """

    @abstractmethod
    def run(self, ctx: Any) -> Any:
        """Execute the task.

        Parameters
        ----------
        ctx: :class:`~pyoco.core.context.Context`
            Execution context providing access to ``inputs``, ``scratch``,
            ``params`` and helper methods such as ``save_artifact``.

        Returns
        -------
        Any
            The value that will be saved to the paths listed in ``outputs``.
        """
        raise NotImplementedError
