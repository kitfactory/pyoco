import os

from ..core.exceptions import OutputWriteError


class SupportInfoWriter:
    def write(self, content: str, output_path: str) -> None:
        try:
            parent = os.path.dirname(output_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as exc:
            raise OutputWriteError(output_path) from exc
