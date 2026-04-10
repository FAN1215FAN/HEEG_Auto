from __future__ import annotations

import platform
import re
import threading
import traceback
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic, perf_counter
from typing import Any

from heeg_auto.config.settings import APP_PATH, ELEMENTS_DIR, PROJECT_ROOT
from heeg_auto.core.actions import ActionExecutor
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger
from heeg_auto.elements import ElementStore
from heeg_auto.runner.case_loader import CONTEXT_KEY_ALIASES, FormalCaseLoader
from heeg_auto.runner.case_resolver import detect_case_format
from heeg_auto.runner.exceptions import ModuleExecutionError
from heeg_auto.runner.module_runner import ModuleRunner
from heeg_auto.v2.case_loader import V2CaseLoader
from heeg_auto.v2.executor import V2CaseExecutor

PARAM_DISPLAY_LABELS = {
    "patient_name": "患者姓名",
    "gender": "性别",
    "habit_hand": "利手",
    "patient_id": "病历号",
    "eeg_id": "脑电号",
    "note": "备注",
    "expect_error_contains": "预期错误包含",
    "device_type": "设备类型",
    "sample_rate": "采样率",
    "baud_rate": "波特率",
    "head_box_number": "头盒数目",
    "ip_address": "IP地址",
    "ip_address_1": "IP地址1",
    "ip_address_2": "IP地址2",
    "port": "端口",
    "device_name": "设备名称",
    "gain_value": "设备增益",
    "exe_path": "软件路径",
    "session_mode": "会话模式",
    "variant_value": "变参值",
}


@dataclass
class _ProgressWatchdog:
    driver: UIADriver
    logger: Any
    timeout_seconds: int = 60

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
        self.element_store = ElementStore(root_dir=ELEMENTS_DIR)
        self.case_loader = FormalCaseLoader()
        self.module_runner = ModuleRunner()
        self.v2_case_loader = V2CaseLoader()
        self.v2_executor = V2CaseExecutor()

    def run_case(
        self,
        case_path: str | Path,
        raise_on_failure: bool = True,
        close_after_run: bool = True,
        stall_timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        if detect_case_format(case_path) == "v2":
            return self._run_v2_case(
                case_path=case_path,
                raise_on_failure=raise_on_failure,
                close_after_run=close_after_run,
                stall_timeout_seconds=stall_timeout_seconds,
            )

        case_data = self.case_loader.load(case_path)
        started_at = datetime.now()
        report_timestamp = started_at.strftime("%Y%m%d_%H%M%S")
        execution_plan = self._build_execution_plan(case_data)
        execution_results: list[dict[str, Any]] = []
        first_failure_exc: Exception | None = None
        halt_reason = ""
        watchdog = _ProgressWatchdog(driver=self.driver, logger=self.logger, timeout_seconds=stall_timeout_seconds)
        watchdog.start()
        watchdog.touch(f"加载用例 {case_data['case_id']}")

        try:
            for execution in execution_plan:
                if halt_reason and case_data.get("stop_on_failure", False):
                    execution_results.append(self._build_not_run_execution(execution, halt_reason))
                    continue
                watchdog.touch(f"准备执行 {execution['execution_name']}")
                result, failure_exc = self._run_execution(case_data, execution, watchdog)
                execution_results.append(result)
                if failure_exc and first_failure_exc is None:
                    first_failure_exc = failure_exc
                if result["status"] in {"FAIL", "INTERRUPTED"} and case_data.get("stop_on_failure", False):
                    halt_reason = "前序执行失败或异常中断，后续轮次按失败即停标记为未执行。"
            finished_at = datetime.now()
            case_result = self._build_case_result(
                case_data=case_data,
                started_at=started_at,
                finished_at=finished_at,
                report_timestamp=report_timestamp,
                execution_results=execution_results,
            )
            if first_failure_exc and raise_on_failure:
                setattr(first_failure_exc, "case_result", case_result)
                raise first_failure_exc
            return case_result
        finally:
            watchdog.stop()
            if close_after_run and self.driver.app is not None:
                self.driver.close()

    def _run_v2_case(
        self,
        case_path: str | Path,
        raise_on_failure: bool = True,
        close_after_run: bool = True,
        stall_timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        case_data = self.v2_case_loader.load(case_path)
        case_data.setdefault("module_chain_labels", ["V2步骤式"])
        started_at = datetime.now()
        watchdog = _ProgressWatchdog(driver=self.driver, logger=self.logger, timeout_seconds=stall_timeout_seconds)
        watchdog.start()
        watchdog.touch(f"加载 V2 用例 {case_data['case_id']}")
        try:
            self._ensure_v2_session(case_data, watchdog)
            result = self.v2_executor.run_case(self.actions, case_data, progress_callback=watchdog.touch)
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
                self._attach_v2_failure_artifacts(case_data, result, first_failure)
                result["error_summary"] = first_failure.get("error_summary", "")
                if raise_on_failure:
                    exc = RuntimeError(first_failure.get("error_summary") or f"V2 用例执行失败：{case_data['case_id']}")
                    setattr(exc, "case_result", result)
                    raise exc
            return result
        finally:
            watchdog.stop()
            if close_after_run and self.driver.app is not None:
                self.driver.close()

    def _ensure_v2_session(self, case_data: dict[str, Any], watchdog: _ProgressWatchdog) -> None:
        for step in case_data.get("steps", []):
            action_name = str(step.get("action", "")).strip()
            if action_name in {"启动应用", "launch_app"}:
                return
        watchdog.touch("连接已有应用会话")
        self.actions.ensure_session(session_mode="复用已有应用")
        watchdog.touch("已连接已有应用会话")

    def _attach_v2_failure_artifacts(
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

    def _run_execution(
        self,
        case_data: dict[str, Any],
        execution: dict[str, Any],
        watchdog: _ProgressWatchdog,
    ) -> tuple[dict[str, Any], Exception | None]:
        execution_started = datetime.now()
        module_results: list[dict[str, Any]] = []
        current_location = case_data["case_id"]
        working_chain = self._build_execution_chain(case_data, execution)
        parameter_snapshot = self._build_parameter_snapshot(working_chain)
        try:
            self._ensure_execution_session(working_chain, watchdog)
            for entry in working_chain:
                current_location = entry["module"]
                watchdog.touch(f"模块开始 {entry['module']}")
                started = perf_counter()
                result = self.module_runner.run_chain(
                    self.actions,
                    self.element_store,
                    [entry],
                    progress_callback=watchdog.touch,
                )[0]
                result["duration_seconds"] = round(perf_counter() - started, 3)
                module_results.append(result)
                watchdog.touch(f"模块完成 {entry['module']}")
            finished_at = datetime.now()
            return (
                self._build_execution_result(
                    execution=execution,
                    started_at=execution_started,
                    finished_at=finished_at,
                    module_results=module_results,
                    status="PASS",
                    error_summary="",
                    error_detail="",
                    failure={},
                    artifact_paths=[],
                    parameter_snapshot=parameter_snapshot,
                ),
                None,
            )
        except Exception as exc:
            status = self._classify_execution_status(exc=exc, watchdog=watchdog)
            failure = self._build_failure_payload(exc, current_location)
            if failure.get("module_result"):
                failure["module_result"]["status"] = status
                module_results.append(failure["module_result"])
            timestamp = f"{case_data['context']['timestamp']}_{execution['sequence']:02d}"
            saved_paths = self.driver.capture_failure_artifacts(
                case_name=execution["execution_id"],
                step_name=failure["failure_location"],
                timestamp=timestamp,
            )
            for path in saved_paths:
                self.logger.error("failure.artifact %s", path)
            finished_at = datetime.now()
            error_summary = watchdog.trigger_reason if watchdog.triggered else str(exc)
            if not error_summary:
                error_summary = exc.__class__.__name__
            result = self._build_execution_result(
                execution=execution,
                started_at=execution_started,
                finished_at=finished_at,
                module_results=module_results,
                status=status,
                error_summary=error_summary,
                error_detail=traceback.format_exc(),
                failure=failure,
                artifact_paths=saved_paths,
                parameter_snapshot=parameter_snapshot,
            )
            return result, exc

    def _ensure_execution_session(self, working_chain: list[dict[str, Any]], watchdog: _ProgressWatchdog) -> None:
        if any(entry.get("module") == "system.launch" for entry in working_chain):
            return
        watchdog.touch("连接已有应用会话")
        self.actions.ensure_session(session_mode="复用已有应用")
        watchdog.touch("已连接已有应用会话")

    def _build_execution_chain(self, case_data: dict[str, Any], execution: dict[str, Any]) -> list[dict[str, Any]]:
        working_chain = deepcopy(case_data["module_chain"])
        execution_context = dict(case_data["context"])
        for item in execution.get("variant_params", []):
            execution_context[item["param"]] = item["value"]
            execution_context[item["param_label"]] = item["value"]
        if len(execution.get("variant_params", [])) == 1:
            only_value = execution["variant_params"][0]["value"]
            execution_context["variant_value"] = only_value
            execution_context["变参值"] = only_value
        return self._resolve_execution_payload(working_chain, execution_context)

    def _build_execution_plan(self, case_data: dict[str, Any]) -> list[dict[str, Any]]:
        variant = case_data.get("variant")
        variant_rows = variant["values"] if variant else [None]
        loop_count = case_data.get("loop_count", 1)
        plan: list[dict[str, Any]] = []
        sequence = 1
        for variant_index, variant_row in enumerate(variant_rows, start=1):
            variant_params = variant_row["display_values"] if variant_row else []
            for loop_index in range(1, loop_count + 1):
                labels = [f"{item['param_label']}={item['value']}" for item in variant_params]
                if loop_count > 1:
                    labels.append(f"第{loop_index}轮")
                suffix = " | ".join(labels)
                plan.append(
                    {
                        "sequence": sequence,
                        "execution_id": f"{case_data['case_id']}#{sequence:02d}",
                        "execution_name": case_data["case_name"] if not suffix else f"{case_data['case_name']} | {suffix}",
                        "loop_index": loop_index,
                        "loop_total": loop_count,
                        "variant": {
                            "module": variant["module"],
                            "module_label": variant["module_label"],
                            "params": variant_params,
                            "index": variant_index,
                            "total": len(variant_rows),
                        }
                        if variant
                        else None,
                        "variant_params": variant_params,
                    }
                )
                sequence += 1
        return plan

    def _build_parameter_snapshot(self, working_chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        for entry in working_chain:
            module_definition = self.module_runner.module_store.load(entry["module"])
            params = []
            for key, value in entry.get("params", {}).items():
                if key == "variant_value":
                    continue
                params.append(
                    {
                        "name": key,
                        "label": PARAM_DISPLAY_LABELS.get(key, key),
                        "value": self._stringify_param_value(value),
                    }
                )
            snapshots.append(
                {
                    "module_id": module_definition["module_id"],
                    "module_label": module_definition["module_label"],
                    "assertion_group": entry.get("assertion_group") or "",
                    "params": params,
                }
            )
        return snapshots

    def _resolve_execution_payload(self, payload, context: dict[str, Any]):
        if isinstance(payload, dict):
            return {key: self._resolve_execution_payload(value, context) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._resolve_execution_payload(item, context) for item in payload]
        if isinstance(payload, str):
            return self._resolve_execution_text(payload, context)
        return payload

    @staticmethod
    def _resolve_execution_text(template: str, context: dict[str, Any]) -> str:
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            raw_key = match.group(1)
            key = CONTEXT_KEY_ALIASES.get(raw_key, raw_key)
            if key not in context:
                raise KeyError(f"未定义变量：{raw_key}")
            value = context[key]
            if isinstance(value, list):
                raise TypeError(f"变量 {raw_key} 是列表，不能直接作为单个文本替换。")
            return str(value)

        return pattern.sub(replace, template)

    @staticmethod
    def _stringify_param_value(value: Any) -> str:
        if isinstance(value, list):
            return "、".join(str(item) for item in value)
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _classify_execution_status(exc: Exception, watchdog: _ProgressWatchdog) -> str:
        if watchdog.triggered:
            return "INTERRUPTED"
        if isinstance(exc, ModuleExecutionError):
            return "FAIL"
        return "INTERRUPTED"

    @staticmethod
    def _build_not_run_execution(execution: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "sequence": execution["sequence"],
            "execution_id": execution["execution_id"],
            "execution_name": execution["execution_name"],
            "loop_index": execution["loop_index"],
            "loop_total": execution["loop_total"],
            "variant": execution.get("variant"),
            "status": "NOT_RUN",
            "passed": False,
            "started_at": "",
            "finished_at": "",
            "duration_seconds": 0,
            "module_results": [],
            "error_summary": reason,
            "error_detail": "",
            "failure": {},
            "artifact_paths": [],
            "parameter_snapshot": [],
        }

    @staticmethod
    def _build_execution_result(
        execution: dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        module_results: list[dict[str, Any]],
        status: str,
        error_summary: str,
        error_detail: str,
        failure: dict[str, Any],
        artifact_paths: list[str | Path],
        parameter_snapshot: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "sequence": execution["sequence"],
            "execution_id": execution["execution_id"],
            "execution_name": execution["execution_name"],
            "loop_index": execution["loop_index"],
            "loop_total": execution["loop_total"],
            "variant": execution.get("variant"),
            "status": status,
            "passed": status == "PASS",
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "module_results": module_results,
            "error_summary": error_summary,
            "error_detail": error_detail,
            "failure": {k: v for k, v in failure.items() if k != "module_result"},
            "artifact_paths": [str(path) for path in artifact_paths],
            "parameter_snapshot": parameter_snapshot,
        }

    def _build_case_result(
        self,
        case_data: dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        report_timestamp: str,
        execution_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        first_abnormal = next(
            (item for item in execution_results if item["status"] in {"FAIL", "INTERRUPTED"}),
            None,
        )
        artifact_paths = [path for item in execution_results for path in item.get("artifact_paths", [])]
        passed_runs = sum(1 for item in execution_results if item["status"] == "PASS")
        failed_runs = sum(1 for item in execution_results if item["status"] == "FAIL")
        interrupted_runs = sum(1 for item in execution_results if item["status"] == "INTERRUPTED")
        not_run_runs = sum(1 for item in execution_results if item["status"] == "NOT_RUN")
        executed_runs = passed_runs + failed_runs + interrupted_runs
        if interrupted_runs > 0:
            status = "INTERRUPTED"
        elif failed_runs > 0:
            status = "FAIL"
        else:
            status = "PASS"
        return {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "tags": case_data.get("tags", []),
            "module_chain_labels": case_data.get("module_chain_labels", []),
            "variant": case_data.get("variant"),
            "loop_count": case_data.get("loop_count", 1),
            "stop_on_failure": case_data.get("stop_on_failure", False),
            "passed": status == "PASS",
            "status": status,
            "context": case_data["context"],
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "report_timestamp": report_timestamp,
            "execution_results": execution_results,
            "summary": {
                "planned_runs": len(execution_results),
                "executed_runs": executed_runs,
                "passed_runs": passed_runs,
                "failed_runs": failed_runs,
                "interrupted_runs": interrupted_runs,
                "not_run_runs": not_run_runs,
            },
            "module_results": execution_results[0]["module_results"] if len(execution_results) == 1 else [],
            "error_summary": first_abnormal["error_summary"] if first_abnormal else "",
            "error_detail": first_abnormal.get("error_detail", "") if first_abnormal else "",
            "failure": first_abnormal.get("failure", {}) if first_abnormal else {},
            "artifact_paths": artifact_paths,
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
                    "assertion_group": "",
                    "status": "FAIL",
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
                "assertion_group": "",
                "status": "INTERRUPTED",
                "failed_step": "",
                "step_results": [],
                "duration_seconds": 0,
            },
        }
