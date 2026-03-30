from __future__ import annotations

import platform
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from heeg_auto.config.settings import APP_PATH, ELEMENTS_DIR, PROJECT_ROOT
from heeg_auto.core.actions import ActionExecutor
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger
from heeg_auto.elements import ElementStore
from heeg_auto.runner.case_loader import FormalCaseLoader
from heeg_auto.runner.exceptions import ModuleExecutionError
from heeg_auto.runner.module_runner import ModuleRunner

LAUNCH_RESULT_MAP = {
    "launch": ("system.launch", "\u7cfb\u7edf\u542f\u52a8"),
    "attach": ("system.attach", "\u8fde\u63a5\u5df2\u6709\u5e94\u7528"),
    "reuse": ("system.reuse", "\u590d\u7528\u5f53\u524d\u4f1a\u8bdd"),
}


class FormalCaseRunner:
    def __init__(self) -> None:
        self.logger = build_logger()
        self.driver = UIADriver(logger=self.logger)
        self.actions = ActionExecutor(driver=self.driver, logger=self.logger)
        self.element_store = ElementStore(root_dir=ELEMENTS_DIR)
        self.case_loader = FormalCaseLoader()
        self.module_runner = ModuleRunner()

    def run_case(self, case_path: str | Path, raise_on_failure: bool = True, close_after_run: bool = True) -> dict[str, Any]:
        case_data = self.case_loader.load(case_path)
        case_id = case_data["case_id"]
        started_at = datetime.now()
        report_timestamp = started_at.strftime("%Y%m%d_%H%M%S")
        module_results: list[dict[str, Any]] = []
        current_location = "system.launch"

        try:
            launch_started = perf_counter()
            launch_mode = self.actions.ensure_session(case_data.get("session_policy", "\u81ea\u52a8"))
            launch_module_id, launch_module_label = LAUNCH_RESULT_MAP[launch_mode]
            module_results.append(
                {
                    "module_id": launch_module_id,
                    "module_label": launch_module_label,
                    "status": "PASS",
                    "expected_status": "PASS",
                    "duration_seconds": round(perf_counter() - launch_started, 3),
                    "failed_step": "",
                    "step_results": [],
                }
            )

            for entry in case_data["module_chain"]:
                current_location = entry["module"]
                started = perf_counter()
                result = self.module_runner.run_chain(self.actions, self.element_store, [entry])[0]
                result["duration_seconds"] = round(perf_counter() - started, 3)
                module_results.append(result)

            finished_at = datetime.now()
            return self._build_result(
                case_data=case_data,
                started_at=started_at,
                finished_at=finished_at,
                report_timestamp=report_timestamp,
                module_results=module_results,
                passed=True,
                error_summary="",
                error_detail="",
                failure={},
                artifact_paths=[],
            )
        except Exception as exc:
            failure = self._build_failure_payload(exc, current_location)
            if failure.get("module_result"):
                module_results.append(failure["module_result"])
            saved_paths = self.driver.capture_failure_artifacts(
                case_name=case_id,
                step_name=failure["failure_location"],
                timestamp=case_data["context"]["timestamp"],
            )
            for path in saved_paths:
                self.logger.error("failure.artifact %s", path)
            finished_at = datetime.now()
            result = self._build_result(
                case_data=case_data,
                started_at=started_at,
                finished_at=finished_at,
                report_timestamp=report_timestamp,
                module_results=module_results,
                passed=False,
                error_summary=str(exc),
                error_detail=traceback.format_exc(),
                failure=failure,
                artifact_paths=saved_paths,
            )
            if raise_on_failure:
                setattr(exc, "case_result", result)
                raise
            return result
        finally:
            if close_after_run:
                self.driver.close()

    def _build_result(
        self,
        case_data: dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        report_timestamp: str,
        module_results: list[dict[str, Any]],
        passed: bool,
        error_summary: str,
        error_detail: str,
        failure: dict[str, Any],
        artifact_paths: list[str],
    ) -> dict[str, Any]:
        return {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "tags": case_data.get("tags", []),
            "session_policy": case_data.get("session_policy", "\u81ea\u52a8"),
            "module_chain_labels": case_data.get("module_chain_labels", []),
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
            "context": case_data["context"],
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "report_timestamp": report_timestamp,
            "module_results": module_results,
            "error_summary": error_summary,
            "error_detail": error_detail,
            "failure": {k: v for k, v in failure.items() if k != "module_result"},
            "artifact_paths": [str(path) for path in artifact_paths],
            "environment": {
                "app_path": str(APP_PATH),
                "case_path": case_data["case_path"],
                "cwd": str(PROJECT_ROOT),
                "python_version": platform.python_version(),
            },
        }

    @staticmethod
    def _build_failure_payload(exc: Exception, current_location: str) -> dict[str, Any]:
        if isinstance(exc, ModuleExecutionError):
            return {
                "module_id": exc.module_id,
                "module_label": exc.module_label,
                "failed_step": exc.failed_step,
                "failure_location": f"{exc.module_id}.{exc.failed_step}",
                "module_result": {
                    "module_id": exc.module_id,
                    "module_label": exc.module_label,
                    "status": "FAIL",
                    "expected_status": "UNKNOWN",
                    "failed_step": exc.failed_step,
                    "step_results": exc.step_results,
                    "duration_seconds": 0,
                },
            }
        return {
            "module_id": current_location,
            "module_label": current_location,
            "failed_step": "",
            "failure_location": current_location,
            "module_result": {
                "module_id": current_location,
                "module_label": current_location,
                "status": "FAIL",
                "expected_status": "UNKNOWN",
                "failed_step": "",
                "step_results": [],
                "duration_seconds": 0,
            },
        }
