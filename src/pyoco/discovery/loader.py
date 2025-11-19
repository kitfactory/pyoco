import importlib
import pkgutil
import sys
from typing import Dict, List, Any
from ..core.models import Task
from ..dsl.syntax import TaskWrapper

class TaskLoader:
    def __init__(self, config: Any):
        self.config = config
        self.tasks: Dict[str, Task] = {}

    def load(self):
        # Load from packages
        for package in self.config.discovery.packages:
            self._load_package(package)
        
        # Load from entry points (simplified)
        for ep in self.config.discovery.entry_points:
            # Assuming ep is a module path for now
            self._load_module(ep)
            
        # Load explicitly defined tasks in config
        for task_name, task_conf in self.config.tasks.items():
            self._load_explicit_task(task_name, task_conf)

    def _load_package(self, package_name: str):
        try:
            pkg = importlib.import_module(package_name)
            # Walk packages if needed, or just import the top level
            # For MVP, let's assume tasks are exposed or we scan modules
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

    def _scan_module(self, module: Any):
        for name, obj in vars(module).items():
            if isinstance(obj, TaskWrapper):
                self.tasks[name] = obj.task
            elif isinstance(obj, Task):
                self.tasks[name] = obj
            # Also check for functions with __pyoco_task__ attr if we used that approach
            elif callable(obj) and getattr(obj, '__pyoco_task__', False):
                # Convert to Task if not already
                pass

    def _load_explicit_task(self, name: str, conf: Any):
        # Load callable
        module_path, func_name = conf.callable.split(':')
        try:
            mod = importlib.import_module(module_path)
            func = getattr(mod, func_name)
            # Create a Task wrapper
            t = Task(func=func, name=name)
            self.tasks[name] = t
        except (ImportError, AttributeError) as e:
            print(f"Error loading task {name}: {e}")

    def get_task(self, name: str) -> Task:
        return self.tasks.get(name)
