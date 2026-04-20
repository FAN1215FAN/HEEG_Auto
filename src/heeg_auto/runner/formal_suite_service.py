from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from heeg_auto.config.settings import DEFAULT_ENVIRONMENT_MODE, DEFAULT_STALL_TIMEOUT
from heeg_auto.core.reporting import generate_suite_reports
from heeg_auto.runner.directory_lifecycle import DirectoryLifecycleManager
from heeg_auto.runner.formal_case_runner import FormalCaseRunner

ProgressCallback = Callable[[int, int, dict[str, Any], dict[str, Any]], None]


class FormalSuiteService:
    def __init__(
        self,
        runner: FormalCaseRunner | None = None,
        lifecycle: DirectoryLifecycleManager | None = None,
        stall_timeout_seconds: int = DEFAULT_STALL_TIMEOUT,
        close_driver_on_finish: bool = True,
        environment_mode: str = DEFAULT_ENVIRONMENT_MODE,
    ) -> None:
        self.runner = runner or FormalCaseRunner()
        self.stall_timeout_seconds = stall_timeout_seconds
        self.lifecycle = lifecycle or DirectoryLifecycleManager(
            runner=self.runner,
            stall_timeout_seconds=stall_timeout_seconds,
            environment_mode=environment_mode,
        )
        self.close_driver_on_finish = close_driver_on_finish
        self.environment_mode = environment_mode
        self._finished = False

    def run_case_item(self, item: dict[str, Any]) -> dict[str, Any]:
        case_path = item["path"]
        try:
            self.lifecycle.prepare_for_case(case_path)
            result = self.runner.run_case(
                case_path,
                raise_on_failure=False,
                close_after_run=False,
                stall_timeout_seconds=self.stall_timeout_seconds,
            )
        except Exception as exc:
            result = self.build_loader_failure_result(item, exc)
        self.lifecycle.record_case_result(case_path, result)
        result["relative_dir"] = item.get("relative_dir", result.get("relative_dir", ""))
        return result

    def execute_suite(
        self,
        items: list[dict[str, Any]],
        progress_callback: ProgressCallback | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for index, item in enumerate(items, start=1):
            result = self.run_case_item(item)
            results.append(result)
            if progress_callback is not None:
                progress_callback(index, len(items), item, result)
        return results

    def finalize_suite(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        report_files = generate_suite_reports(results)
        passed_cases = sum(1 for item in results if item.get("status") == "PASS")
        failed_cases = sum(1 for item in results if item.get("status") == "FAIL")
        interrupted_cases = sum(1 for item in results if item.get("status") == "INTERRUPTED")
        return {
            "report_files": report_files,
            "passed_cases": passed_cases,
            "failed_cases": failed_cases,
            "interrupted_cases": interrupted_cases,
        }

    def finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.lifecycle.finish()
        if self.close_driver_on_finish:
            self.runner.driver.close()

    @staticmethod
    def build_loader_failure_result(item: dict[str, Any], exc: Exception) -> dict[str, Any]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "case_id": item["case_id"],
            "case_name": item["case_name"],
            "case_path": str(item["path"]),
            "relative_dir": item["relative_dir"],
            "tags": item.get("tags", []),
            "module_chain_labels": item.get("module_chain_labels", []),
            "variant": item.get("variant"),
            "loop_count": item.get("loop_count", 1),
            "stop_on_failure": True,
            "passed": False,
            "status": "INTERRUPTED",
            "context": {},
            "started_at": now,
            "finished_at": now,
            "duration_seconds": 0,
            "report_timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "execution_results": [
                {
                    "sequence": 1,
                    "execution_id": f"{item['case_id']}#01",
                    "execution_name": item["case_name"],
                    "loop_index": 1,
                    "loop_total": 1,
                    "variant": None,
                    "status": "INTERRUPTED",
                    "passed": False,
                    "started_at": now,
                    "finished_at": now,
                    "duration_seconds": 0,
                    "module_results": [],
                    "error_summary": str(exc) or exc.__class__.__name__,
                    "error_detail": traceback.format_exc(),
                    "failure": {},
                    "artifact_paths": [],
                    "parameter_snapshot": [],
                }
            ],
            "summary": {
                "planned_runs": 1,
                "executed_runs": 1,
                "passed_runs": 0,
                "failed_runs": 0,
                "interrupted_runs": 1,
                "not_run_runs": 0,
            },
            "module_results": [],
            "error_summary": str(exc) or exc.__class__.__name__,
            "error_detail": traceback.format_exc(),
            "failure": {},
            "artifact_paths": [],
            "environment": {},
        }

