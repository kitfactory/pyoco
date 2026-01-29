from ..core.exceptions import InvalidFilterError
from ..core.models import SupportFilters
from .collector import TaskInfoCollector
from .filters import normalize_filters, validate_filters
from .renderer import SupportInfoRenderer
from .writer import SupportInfoWriter


class SupportInfoService:
    def __init__(
        self,
        collector: TaskInfoCollector | None = None,
        renderer: SupportInfoRenderer | None = None,
        writer: SupportInfoWriter | None = None,
    ) -> None:
        self.collector = collector or TaskInfoCollector()
        self.renderer = renderer or SupportInfoRenderer()
        self.writer = writer or SupportInfoWriter()

    def build(
        self,
        *,
        kind: str,
        config_path: str,
        format: str = "prompt",
        filters: SupportFilters | None = None,
        output_path: str | None = None,
    ) -> str:
        normalized = normalize_filters(filters)
        validate_filters(normalized)

        if kind == "task" and not normalized.name:
            raise InvalidFilterError("name")

        tasks = []
        if kind in ("tasks", "task"):
            tasks = self.collector.collect(config_path, normalized)

        content = self.renderer.render(kind, tasks, format)
        if output_path:
            self.writer.write(content, output_path)
        return content
