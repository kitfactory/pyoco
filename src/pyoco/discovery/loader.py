import importlib
import os
from dataclasses import asdict, is_dataclass
from typing import Dict, List, Any, Set
from ..core.models import Task
from ..dsl.syntax import TaskWrapper
from .plugins import PluginRegistry, entry_point_version, iter_entry_points

class TaskLoader:
    def __init__(self, config: Any, strict: bool = False):
        self.config = config
        self.strict = strict
        self.tasks: Dict[str, Task] = {}
        self.task_infos: Dict[str, Any] = {}
        self._explicit_tasks: Set[str] = set()
        self.plugin_reports: List[Dict[str, Any]] = []

    def load(self):
        # Load explicitly defined tasks in config FIRST (Higher priority)
        for task_name, task_conf in self.config.tasks.items():
            callable_path = self._conf_get(task_conf, "callable")
            if callable_path:
                self._load_explicit_task(task_name, task_conf, callable_path)
                self._explicit_tasks.add(task_name)

        self._load_env_modules()

        self._load_entry_point_plugins()

    def _load_env_modules(self) -> None:
        raw = os.getenv("PYOCO_DISCOVERY_MODULES", "")
        modules = [item.strip() for item in raw.replace(",", " ").split() if item.strip()]
        for module_name in modules:
            self._load_module(module_name)

    def _register_task(self, name: str, task: Task):
        if name in self.tasks:
            if name in self._explicit_tasks:
                # Explicit wins, ignore implicit
                return
            
            # Collision between implicits
            msg = f"Task '{name}' already defined."
            if self.strict:
                raise ValueError(f"{msg} (Strict mode enabled)")
            else:
                print(f"Warning: {msg} Overwriting.")
        
        # Apply config overlay if exists
        if self.config and name in self.config.tasks:
            conf = self.config.tasks[name]
            if not self._conf_get(conf, "callable"):
                inputs = self._conf_get(conf, "inputs") or {}
                outputs = self._conf_get(conf, "outputs") or []
                if inputs:
                    task.inputs.update(inputs)
                if outputs:
                    task.outputs.extend(outputs)

        self.tasks[name] = task

    def _register_task_info(self, info: Any):
        name = getattr(info, "name", None)
        if not name:
            return
        if name in self.task_infos:
            msg = f"Task metadata '{name}' already defined."
            if self.strict:
                raise ValueError(f"{msg} (Strict mode enabled)")
            else:
                print(f"Warning: {msg} Overwriting.")
        self.task_infos[name] = info

    def _load_module(self, module_name: str):
        try:
            mod = importlib.import_module(module_name)
            self._scan_module(mod)
        except ImportError as e:
            print(f"Warning: Could not import module {module_name}: {e}")

    def _load_entry_point_plugins(self):
        entries = iter_entry_points()
        for ep in entries:
            info = {
                "name": ep.name,
                "version": entry_point_version(ep),
                "value": ep.value,
                "module": getattr(ep, "module", ""),
                "tasks": [],
                "warnings": [],
            }
            registry = PluginRegistry(self, ep.name)
            try:
                hook = ep.load()
                if not callable(hook):
                    raise TypeError("Entry point must be callable")
                hook(registry)
                info["tasks"] = list(registry.records)
                info["task_infos"] = [self._serialize_task_info(item) for item in registry.task_infos.values()]
                info["warnings"] = list(registry.warnings)
                if not registry.records:
                    info["warnings"].append("no tasks registered")
            except Exception as exc:
                info["error"] = str(exc)
                if self.strict:
                    raise
                print(f"Warning: Plugin '{ep.name}' failed to load: {exc}")
            self.plugin_reports.append(info)

    def _serialize_task_info(self, task_info: Any) -> Dict[str, Any]:
        if is_dataclass(task_info):
            return asdict(task_info)
        if isinstance(task_info, dict):
            return task_info
        return {"name": getattr(task_info, "name", "<unknown>")}

    def _scan_module(self, module: Any):
        for name, obj in vars(module).items():
            if isinstance(obj, TaskWrapper):
                self._register_task(name, obj.task)
            elif isinstance(obj, Task):
                self._register_task(name, obj)

    def _conf_get(self, conf: Any, key: str):
        if hasattr(conf, key):
            return getattr(conf, key)
        if isinstance(conf, dict):
            return conf.get(key)
        return None

    def _load_explicit_task(self, name: str, conf: Any, callable_path: str):
        # Load callable
        module_path, func_name = callable_path.split(':')
        try:
            mod = importlib.import_module(module_path)
            obj = getattr(mod, func_name)
            
            # Unwrap if it's a TaskWrapper or Task
            real_func = obj
            if isinstance(obj, TaskWrapper):
                real_func = obj.task.func
            elif isinstance(obj, Task):
                real_func = obj.func
                
            # Create a Task wrapper
            t = Task(func=real_func, name=name)
            t.inputs = self._conf_get(conf, "inputs") or {}
            t.outputs = self._conf_get(conf, "outputs") or []
            self.tasks[name] = t
        except (ImportError, AttributeError) as e:
            print(f"Error loading task {name}: {e}")

    def get_task(self, name: str) -> Task:
        return self.tasks.get(name)
