from __future__ import annotations

import platform
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

from heeg_auto.config.settings import APP_PATH, PROJECT_ROOT
from heeg_auto.config.settings import DEFAULT_STALL_TIMEOUT
from heeg_auto.core.actions import ActionExecutor
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger
from heeg_auto.runner.step_case_executor import StepCaseExecutor
from heeg_auto.runner.step_case_loader import StepCaseLoader


@dataclass
class _ProgressWatchdog:
    driver: UIADriver
    logger: Any
    timeout_seconds: int = DEFAULT_STALL_TIMEOUT

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._last_progress_at = monotonic()
        self._last_label = "初始化"
        self.triggered = False
        self.trigger_reason = ""
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def touch(self, label: str) -> None:
        with self._lock:
            self._last_progress_at = monotonic()
            self._last_label = label

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.wait(1):
            with self._lock:
                idle_seconds = monotonic() - self._last_progress_at
                label = self._last_label
            if idle_seconds < self.timeout_seconds:
                continue
            self.triggered = True
            self.trigger_reason = f"步骤卡住超过 {self.timeout_seconds} 秒：{label}"
            self.logger.error("progress.watchdog %s", self.trigger_reason)
            self.driver.force_close_running_app()
            return


class FormalCaseRunner:
    def __init__(self) -> None:
        self.logger = build_logger()
        self.driver = UIADriver(logger=self.logger)
        self.actions = ActionExecutor(driver=self.driver, logger=self.logger)
        self.step_case_loader = StepCaseLoader()
        self.step_case_executor = StepCaseExecutor()

    def run_case(
        self,
        case_path: str | Path,
        raise_on_failure: bool = True,
        close_after_run: bool = True,
        stall_timeout_seconds: int = DEFAULT_STALL_TIMEOUT,
    ) -> dict[str, Any]:
        case_data = self.step_case_loader.load(case_path)
        case_data.setdefault("module_chain_labels", ["步骤式"])
        started_at = datetime.now()
        watchdog = _ProgressWatchdog(driver=self.driver, logger=self.logger, timeout_seconds=stall_timeout_seconds)
        watchdog.start()
        watchdog.touch(f"加载步骤式用例 {case_data['case_id']}")
        try:
            self._ensure_step_case_session(case_data, watchdog)
            result = self.step_case_executor.run_case(self.actions, case_data, progress_callback=watchdog.touch)
            result["module_chain_labels"] = case_data["module_chain_labels"]
            result["context"] = case_data.get("context", {})
            result["report_timestamp"] = started_at.strftime("%Y%m%d_%H%M%S")
            result.setdefault("artifact_paths", [])
            result.setdefault(
                "environment",
                {
                    "app_path": str(APP_PATH),
                    "case_path": str(case_path),
                    "cwd": str(PROJECT_ROOT),
                    "python_version": platform.python_version(),
                },
            )
            first_failure = next((item for item in result.get("execution_results", []) if item.get("status") == "FAIL"), None)
            if first_failure is not None:
                self._attach_step_case_failure_artifacts(case_data, result, first_failure)
                result["error_summary"] = first_failure.get("error_summary", "")
                if raise_on_failure:
                    exc = RuntimeError(first_failure.get("error_summary") or f"步骤式用例执行失败：{case_data['case_id']}")
                    setattr(exc, "case_result", result)
                    raise exc
            return result
        finally:
            watchdog.stop()
            if close_after_run and self.driver.app is not None:
                self.driver.close()

    def _ensure_step_case_session(self, case_data: dict[str, Any], watchdog: _ProgressWatchdog) -> None:
        for step in case_data.get("steps", []):
            action_name = str(step.get("action", "")).strip()
            if action_name in {"启动应用", "launch_app"}:
                return
        watchdog.touch("连接已有应用会话")
        self.actions.ensure_session(session_mode="复用已有应用")
        watchdog.touch("已连接已有应用会话")

    def _ensure_execution_session(self, entries: list[dict[str, Any]], watchdog: Any) -> None:
        if any(entry.get("module") == "system.launch" for entry in entries):
            return
        watchdog.touch("连接已有应用会话")
        self.actions.ensure_session(session_mode="复用已有应用")
        watchdog.touch("已连接已有应用会话")

    def _attach_step_case_failure_artifacts(
        self,
        case_data: dict[str, Any],
        result: dict[str, Any],
        failed_execution: dict[str, Any],
    ) -> None:
        failed_step = next(
            (item.get("step_name", "") for item in failed_execution.get("step_results", []) if item.get("status") == "FAIL"),
            failed_execution.get("execution_name", case_data["case_id"]),
        )
        timestamp = f"{case_data['context']['timestamp']}_{failed_execution['sequence']:02d}"
        saved_paths = self.driver.capture_failure_artifacts(
            case_name=failed_execution["execution_id"],
            step_name=failed_step,
            timestamp=timestamp,
        )
        failed_execution.setdefault("artifact_paths", [])
        failed_execution["artifact_paths"].extend(str(path) for path in saved_paths)
        result.setdefault("artifact_paths", [])
        result["artifact_paths"].extend(str(path) for path in saved_paths)

    def is_environment_ready(self) -> bool:
        if self.driver.app is None or self.driver.main_window_wrapper is None:
            return False
        try:
            top_window = self.driver.top_window()
            return int(top_window.handle) == int(self.driver.main_window_wrapper.handle)
        except Exception:
            return False
