class ControlFlowError(Exception):
    """Base error for control flow execution issues."""


class UntilMaxIterationsExceeded(ControlFlowError):
    def __init__(self, expression: str, max_iter: int):
        super().__init__(f"Until condition '{expression}' exceeded max_iter={max_iter}")
        self.expression = expression
        self.max_iter = max_iter


class SwitchNoMatch(ControlFlowError):
    def __init__(self, expression: str):
        super().__init__(f"Switch expression '{expression}' did not match any case.")
        self.expression = expression


class SupportInfoError(Exception):
    """Base error for support info generation."""


class InvalidFormatError(SupportInfoError):
    def __init__(self, format: str):
        self.format = format
        super().__init__(f"Invalid format: {format}")


class TaskNotFoundError(SupportInfoError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Task not found: {name}")


class InvalidFilterError(SupportInfoError):
    def __init__(self, filter_value: str):
        self.filter_value = filter_value
        super().__init__(f"Invalid filter: {filter_value}")


class OutputWriteError(SupportInfoError):
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Failed to write output: {path}")


class MissingTaskMetadataError(SupportInfoError):
    def __init__(self, name: str, fields: list[str]):
        self.name = name
        self.fields = fields
        field_list = ",".join(fields)
        super().__init__(f"Missing task metadata: {name} fields={field_list}")
