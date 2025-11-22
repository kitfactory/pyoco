import importlib
import pkgutil
import sys
from typing import Dict, List, Any
from ..core.models import Task
from ..dsl.syntax import TaskWrapper

class TaskLoader:
    def __init__(self, config: Any, strict: bool = False):
        self.config = config
        self.strict = strict
        self.tasks: Dict[str, Task] = {}
        self._explicit_tasks: Set[str] = set()

    def load(self):
        # Load explicitly defined tasks in config FIRST (Higher priority)
        for task_name, task_conf in self.config.tasks.items():
            if task_conf.callable:
                self._load_explicit_task(task_name, task_conf)
                self._explicit_tasks.add(task_name)

        # Load from packages
        for package in self.config.discovery.packages:
            self._load_package(package)
        
        # Load from entry points (simplified)
        for ep in self.config.discovery.entry_points:
            self._load_module(ep)
            
        # Load from glob modules
        for pattern in self.config.discovery.glob_modules:
            self._load_glob_modules(pattern)

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
        if name in self.config.tasks:
            conf = self.config.tasks[name]
            if not conf.callable:
                if conf.inputs:
                    task.inputs.update(conf.inputs)
                if conf.outputs:
                    task.outputs.extend(conf.outputs)

        self.tasks[name] = task

    def _load_package(self, package_name: str):
        try:
            pkg = importlib.import_module(package_name)
            if hasattr(pkg, '__path__'):
                for _, name, _ in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
                    self._load_module(name)
            else:
                self._scan_module(pkg)
        except ImportError as e:
            print(f"Warning: Could not import package {package_name}: {e}")

    def _load_module(self, module_name: str):
        try:
            mod = importlib.import_module(module_name)
            self._scan_module(mod)
        except ImportError as e:
            print(f"Warning: Could not import module {module_name}: {e}")
            
    def _load_glob_modules(self, pattern: str):
        import glob
        import os
        
        # Pattern is likely a file path glob, e.g. "jobs/*.py"
        # We need to convert file paths to module paths
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            if not file_path.endswith(".py"):
                continue
                
            # Convert path to module
            # This is tricky without knowing the root. 
            # Assumption: running from root, and file path is relative to root.
            # e.g. "myproject/tasks/foo.py" -> "myproject.tasks.foo"
            
            rel_path = os.path.relpath(file_path)
            if rel_path.startswith(".."):
                # Out of tree, skip or warn
                continue
                
            module_name = rel_path.replace(os.sep, ".")[:-3] # strip .py
            self._load_module(module_name)

    def _scan_module(self, module: Any):
        for name, obj in vars(module).items():
            if isinstance(obj, TaskWrapper):
                self._register_task(name, obj.task)
            elif isinstance(obj, Task):
                self._register_task(name, obj)
            elif callable(obj) and getattr(obj, '__pyoco_task__', False):
                # Convert to Task if not already
                pass

    def _load_explicit_task(self, name: str, conf: Any):
        # Load callable
        module_path, func_name = conf.callable.split(':')
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
            t.inputs = conf.inputs
            t.inputs = conf.inputs
            t.outputs = conf.outputs
            self.tasks[name] = t
        except (ImportError, AttributeError) as e:
            print(f"Error loading task {name}: {e}")

    def get_task(self, name: str) -> Task:
        return self.tasks.get(name)
