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
