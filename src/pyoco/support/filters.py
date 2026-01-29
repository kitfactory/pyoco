from typing import Any, Iterable, List

from ..core.exceptions import InvalidFilterError
from ..core.models import SupportFilters


def normalize_filters(filters: Any) -> SupportFilters:
    if filters is None:
        return SupportFilters()
    if isinstance(filters, SupportFilters):
        return filters
    if isinstance(filters, dict):
        allowed = {"name", "origin", "tag"}
        extra = set(filters.keys()) - allowed
        if extra:
            raise InvalidFilterError(",".join(sorted(extra)))
        return SupportFilters(
            name=_normalize_list(filters.get("name")),
            origin=_normalize_list(filters.get("origin")),
            tag=_normalize_list(filters.get("tag")),
        )
    raise InvalidFilterError(str(filters))


def validate_filters(filters: SupportFilters) -> None:
    for label, value in ("name", filters.name), ("origin", filters.origin), ("tag", filters.tag):
        if value is None:
            continue
        if not isinstance(value, list) or not value:
            raise InvalidFilterError(label)
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise InvalidFilterError(label)


def filters_label(filters: SupportFilters) -> str:
    parts: List[str] = []
    if filters.name:
        parts.append(f"name={','.join(filters.name)}")
    if filters.origin:
        parts.append(f"origin={','.join(filters.origin)}")
    if filters.tag:
        parts.append(f"tag={','.join(filters.tag)}")
    if not parts:
        return "*"
    return " ".join(parts)


def _normalize_list(value: Any) -> List[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return None
