from typing import List

from ..core.exceptions import MissingTaskMetadataError, TaskNotFoundError
from ..core.models import SupportFilters, TaskInfo
from ..discovery.loader import TaskLoader
from ..schemas.config import PyocoConfig
from .filters import filters_label, normalize_filters, validate_filters


class TaskInfoCollector:
    def collect(self, config_path: str, filters: SupportFilters | None = None) -> List[TaskInfo]:
        normalized = normalize_filters(filters)
        validate_filters(normalized)

        config = PyocoConfig.from_yaml(config_path)
        loader = TaskLoader(config)
        loader.load()

        task_names = sorted(loader.tasks.keys())
        if normalized.name:
            task_names = [name for name in task_names if name in normalized.name]
        if not task_names:
            raise TaskNotFoundError(filters_label(normalized))

        infos: List[TaskInfo] = []
        missing: List[tuple[str, List[str]]] = []
        for name in task_names:
            info = loader.task_infos.get(name)
            if not info:
                missing.append((name, ["summary", "inputs", "outputs"]))
                continue
            missing_fields: List[str] = []
            if not info.summary:
                missing_fields.append("summary")
            if info.inputs is None:
                missing_fields.append("inputs")
            if info.outputs is None:
                missing_fields.append("outputs")
            if missing_fields:
                missing.append((name, missing_fields))
                continue
            infos.append(info)

        if missing:
            name, fields = missing[0]
            raise MissingTaskMetadataError(name, fields)

        if normalized.origin:
            infos = [info for info in infos if info.origin in normalized.origin]
        if normalized.tag:
            infos = [info for info in infos if info.tags and any(tag in info.tags for tag in normalized.tag)]

        if not infos:
            raise TaskNotFoundError(filters_label(normalized))

        return infos
