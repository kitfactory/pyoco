from __future__ import annotations

from importlib import metadata as importlib_metadata
from typing import Any, Callable, Dict, List, Optional, Type

from ..core.models import Task, TaskInfo, TaskIO
from ..core.exceptions import MissingTaskMetadataError
from ..dsl.syntax import TaskWrapper


class CallablePluginTask(Task):
    """Lightweight subclass so callable registrations still appear as Task-derived."""

    def __init__(self, func: Callable, name: str):
        super().__init__(func=func, name=name)


def iter_entry_points(group: str = "pyoco.tasks"):
    eps = importlib_metadata.entry_points()
    if hasattr(eps, "select"):
        return list(eps.select(group=group))
    return list(eps.get(group, []))


def list_available_plugins() -> List[Dict[str, Any]]:
    plugins = []
    for ep in iter_entry_points():
        plugins.append(
            {
                "name": ep.name,
                "module": getattr(ep, "module", ""),
                "value": ep.value,
            }
        )
    return plugins


class PluginRegistry:
    def __init__(self, loader: Any, provider_name: str) -> None:
        self.loader = loader
        self.provider_name = provider_name
        self.registered_names: List[str] = []
        self.records: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.task_infos: Dict[str, TaskInfo] = {}

    def task_info(
        self,
        *,
        name: Optional[str] = None,
        summary: Optional[str] = None,
        inputs: Optional[List[Any]] = None,
        outputs: Optional[List[Any]] = None,
        tags: Optional[List[str]] = None,
        origin: Optional[str] = None,
    ) -> None:
        missing = []
        if not name:
            missing.append("name")
        if not summary:
            missing.append("summary")
        if inputs is None:
            missing.append("inputs")
        if outputs is None:
            missing.append("outputs")
        if missing:
            raise MissingTaskMetadataError(name or "<unknown>", missing)

        if not isinstance(inputs, list) or not isinstance(outputs, list):
            raise MissingTaskMetadataError(name, ["inputs", "outputs"])
        task_inputs = self._normalize_taskio_list(inputs, "inputs", name)
        task_outputs = self._normalize_taskio_list(outputs, "outputs", name)
        info = TaskInfo(
            name=name,
            summary=summary,
            inputs=task_inputs,
            outputs=task_outputs,
            origin=origin or self.provider_name,
            tags=tags or [],
        )
        self.task_infos[name] = info
        if hasattr(self.loader, "_register_task_info"):
            self.loader._register_task_info(info)

    def task(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[List[str]] = None,
    ):
        if func is not None:
            self.register_callable(
                func,
                name=name,
                inputs=inputs or {},
                outputs=outputs or [],
            )
            return func

        def decorator(inner: Callable):
            self.register_callable(
                inner,
                name=name,
                inputs=inputs or {},
                outputs=outputs or [],
            )
            return inner

        return decorator

    def register_callable(
        self,
        func: Callable,
        *,
        name: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[List[str]] = None,
    ) -> Task:
        task_name = name or getattr(func, "__name__", f"{self.provider_name}_task")
        task = CallablePluginTask(func=func, name=task_name)
        if inputs:
            task.inputs.update(inputs)
        if outputs:
            task.outputs.extend(outputs)
        self._finalize_task(task, origin="callable")
        return task

    def task_class(
        self,
        task_cls: Type[Task],
        *args: Any,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Task:
        if not issubclass(task_cls, Task):
            raise TypeError(f"{task_cls} is not a Task subclass")
        task = task_cls(*args, **kwargs)
        if name:
            task.name = name
        self._finalize_task(task, origin="task_class")
        return task

    def add(self, obj: Any, *, name: Optional[str] = None) -> None:
        if isinstance(obj, TaskWrapper):
            task = obj.task
            if name:
                task.name = name
            self._finalize_task(task, origin="wrapper")
        elif isinstance(obj, Task):
            if name:
                obj.name = name
            origin = "task_class" if obj.__class__ is not Task else "task"
            self._finalize_task(obj, origin=origin)
        elif callable(obj):
            self.register_callable(obj, name=name)
        else:
            raise TypeError(f"Unsupported task object: {obj!r}")

    def _finalize_task(self, task: Task, origin: str) -> None:
        warnings = self._validate_task(task, origin)
        self.loader._register_task(task.name, task)
        self.registered_names.append(task.name)
        self.records.append(
            {
                "name": task.name,
                "origin": origin,
                "class": task.__class__.__name__,
                "warnings": warnings,
            }
        )
        for msg in warnings:
            self.warnings.append(f"{task.name}: {msg}")

    def _validate_task(self, task: Task, origin: str) -> List[str]:
        warnings: List[str] = []
        if not getattr(task, "name", None):
            generated = f"{self.provider_name}_{len(self.registered_names) + 1}"
            task.name = generated
            warnings.append(f"name missing; auto-assigned '{generated}'")
        if not callable(getattr(task, "func", None)):
            warnings.append("task.func is not callable")
        if origin == "callable":
            warnings.append("registered via callable; prefer Task subclass for extensibility")
        if task.__class__ is Task and origin not in ("callable", "wrapper"):
            warnings.append("plain Task instance detected; subclass Task for metadata support")
        return warnings

    def _normalize_taskio_list(self, items: List[Any], label: str, task_name: str) -> List[TaskIO]:
        normalized: List[TaskIO] = []
        for idx, item in enumerate(items):
            if isinstance(item, TaskIO):
                normalized.append(item)
                continue
            if isinstance(item, dict):
                taskio = TaskIO.from_dict(item)
                missing = []
                if not taskio.name:
                    missing.append(f"{label}[{idx}].name")
                if not taskio.type:
                    missing.append(f"{label}[{idx}].type")
                if taskio.required is None:
                    missing.append(f"{label}[{idx}].required")
                if missing:
                    raise MissingTaskMetadataError(task_name, missing)
                normalized.append(taskio)
                continue
            raise MissingTaskMetadataError(task_name, [f"{label}[{idx}]"])
        return normalized
