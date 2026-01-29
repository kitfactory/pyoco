from .service import SupportInfoService


def build(
    kind: str,
    config_path: str,
    format: str = "prompt",
    filters=None,
    output_path: str | None = None,
):
    service = SupportInfoService()
    return service.build(
        kind=kind,
        config_path=config_path,
        format=format,
        filters=filters,
        output_path=output_path,
    )


__all__ = ["SupportInfoService", "build"]
