from __future__ import annotations

from typing import Optional

from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from ..core.models import RunStatus


_DEFAULT_BUCKETS = (
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)


class MetricsSink:
    """
    Small wrapper that owns a CollectorRegistry so tests can reset easily.
    """

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self) -> None:
        self.runs_total = Counter(
            "pyoco_runs_total",
            "Total runs observed by status transitions.",
            ["status"],
            registry=self.registry,
        )
        self.runs_in_progress = Gauge(
            "pyoco_runs_in_progress",
            "Number of runs currently executing (RUNNING).",
            registry=self.registry,
        )
        self.task_duration = Histogram(
            "pyoco_task_duration_seconds",
            "Observed task durations.",
            ["task"],
            buckets=_DEFAULT_BUCKETS,
            registry=self.registry,
        )
        self.run_duration = Histogram(
            "pyoco_run_duration_seconds",
            "Observed end-to-end run durations.",
            ["flow"],
            buckets=_DEFAULT_BUCKETS,
            registry=self.registry,
        )

    def reset(self) -> None:
        self.__init__()

    def record_status_transition(
        self,
        previous: Optional[RunStatus],
        new_status: RunStatus,
    ) -> None:
        status_value = new_status.value if hasattr(new_status, "value") else str(new_status)
        self.runs_total.labels(status=status_value).inc()

        prev_value = previous.value if hasattr(previous, "value") else previous
        if status_value == RunStatus.RUNNING.value:
            if prev_value != RunStatus.RUNNING.value:
                self.runs_in_progress.inc()
        elif prev_value == RunStatus.RUNNING.value:
            self.runs_in_progress.dec()

    def record_task_duration(self, task_name: str, duration_ms: Optional[float]) -> None:
        if duration_ms is None:
            return
        if duration_ms < 0:
            return
        self.task_duration.labels(task=task_name).observe(duration_ms / 1000.0)

    def record_run_duration(
        self,
        flow_name: str,
        start_time: Optional[float],
        end_time: Optional[float],
    ) -> None:
        if start_time is None or end_time is None:
            return
        duration = end_time - start_time
        if duration < 0:
            return
        self.run_duration.labels(flow=flow_name).observe(duration)

    def render_latest(self) -> bytes:
        return generate_latest(self.registry)


metrics = MetricsSink()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
