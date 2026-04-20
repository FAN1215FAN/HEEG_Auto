from __future__ import annotations


class ModuleExecutionError(RuntimeError):
    def __init__(
        self,
        module_id: str,
        module_label: str,
        failed_step: str,
        message: str,
        step_results: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.module_id = module_id
        self.module_label = module_label
        self.failed_step = failed_step
        self.step_results = step_results or []
