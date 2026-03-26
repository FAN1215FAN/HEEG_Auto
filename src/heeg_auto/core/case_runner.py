from __future__ import annotations

import json
import platform
import re
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from heeg_auto.config.settings import APP_PATH, PROJECT_ROOT
from heeg_auto.core.actions import ActionExecutor
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.line_dsl import LineDslCompiler
from heeg_auto.core.logger import build_logger


class CaseRunner:
    def __init__(self) -> None:
        self.logger = build_logger()
        self.driver = UIADriver(logger=self.logger)
        self.executor = ActionExecutor(driver=self.driver, logger=self.logger)

    def run_case(self, case_path: str | Path, raise_on_failure: bool = True) -> dict[str, Any]:
        case_file = Path(case_path)
        case_data = self._load_case(case_file)
        context = self._build_context(case_data.get("data", {}))
        case_name = case_data["case_name"]
        description = case_data.get("description", "")
        started_at = datetime.now()
        report_timestamp = started_at.strftime("%Y%m%d_%H%M%S")
        steps: list[dict[str, Any]] = []
        self.logger.info("Running case: %s", case_name)

        current_action_name = "load_case"
        current_step_index = 0

        try:
            for index, raw_step in enumerate(case_data["steps"], start=1):
                current_step_index = index
                step_started_at = datetime.now()
                step_started_perf = perf_counter()
                # 每一步都记录动作、参数、耗时和结果，后续统一用于 JSON/Word 报告输出。
                step_record: dict[str, Any] = {
                    "index": index,
                    "action": "",
                    "resolved_action": "",
                    "target": "-",
                    "parameters": "-",
                    "status": "RUNNING",
                    "started_at": step_started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "finished_at": "",
                    "duration_seconds": 0,
                    "error_summary": "",
                }

                try:
                    step = self._resolve_payload(raw_step, context)
                    requested_action = step.pop("action")
                    current_action_name = requested_action
                    action_name = self.executor.resolve_action_name(requested_action)
                    step_record["action"] = requested_action
                    step_record["resolved_action"] = action_name
                    step_record["target"] = self._extract_target(step)
                    step_record["parameters"] = self._summarize_parameters(step)
                    self.logger.info("Execute step: %s -> %s | %s", requested_action, action_name, step)
                    action = getattr(self.executor, action_name)
                    action(**step)
                    step_record["status"] = "PASS"
                except Exception as step_error:
                    # 不在这里吞异常，而是先把当前步骤记成 FAIL，再交给外层统一截图和生成失败结果。
                    step_record["status"] = "FAIL"
                    step_record["error_summary"] = str(step_error)
                    if not step_record["action"] and isinstance(raw_step, dict):
                        step_record["action"] = str(raw_step.get("action", ""))
                    raise
                finally:
                    step_finished_at = datetime.now()
                    step_record["finished_at"] = step_finished_at.strftime("%Y-%m-%d %H:%M:%S")
                    step_record["duration_seconds"] = round(perf_counter() - step_started_perf, 3)
                    steps.append(step_record)

            finished_at = datetime.now()
            return self._build_result(
                case_name=case_name,
                case_file=case_file,
                description=description,
                context=context,
                started_at=started_at,
                finished_at=finished_at,
                report_timestamp=report_timestamp,
                steps=steps,
                passed=True,
                error_summary="",
                error_detail="",
                artifact_paths=[],
            )
        except Exception as exc:
            saved_paths = self.driver.capture_failure_artifacts(
                case_name=case_name,
                step_name=current_action_name,
                step_index=current_step_index,
                timestamp=context["timestamp"],
            )
            for path in saved_paths:
                self.logger.error("failure.artifact %s", path)
            finished_at = datetime.now()
            result = self._build_result(
                case_name=case_name,
                case_file=case_file,
                description=description,
                context=context,
                started_at=started_at,
                finished_at=finished_at,
                report_timestamp=report_timestamp,
                steps=steps,
                passed=False,
                error_summary=str(exc),
                error_detail=traceback.format_exc(),
                artifact_paths=saved_paths,
            )
            if raise_on_failure:
                setattr(exc, "case_result", result)
                raise
            return result
        finally:
            self.driver.close()

    def _build_result(
        self,
        case_name: str,
        case_file: Path,
        description: str,
        context: dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        report_timestamp: str,
        steps: list[dict[str, Any]],
        passed: bool,
        error_summary: str,
        error_detail: str,
        artifact_paths: list[Path],
    ) -> dict[str, Any]:
        return {
            "case_name": case_name,
            "case_path": str(case_file),
            "description": description,
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
            "context": context,
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "report_timestamp": report_timestamp,
            "steps": steps,
            "error_summary": error_summary,
            "error_detail": error_detail,
            "artifact_paths": [str(path) for path in artifact_paths],
            "environment": {
                "app_path": str(APP_PATH),
                "case_path": str(case_file),
                "cwd": str(PROJECT_ROOT),
                "python_version": platform.python_version(),
            },
        }

    def _load_case(self, case_file: Path) -> dict:
        content = case_file.read_text(encoding="utf-8-sig")
        suffix = case_file.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(content)
        if suffix in {".zh", ".txt", ".steps"}:
            return LineDslCompiler().compile_to_case(content, default_case_name=case_file.stem)

        raise ValueError(f"Unsupported case file extension: {case_file.suffix}")

    def _build_context(self, data: dict) -> dict:
        # timestamp 作为全局根变量，后续可被患者名、病历号、脑电号等多个字段复用。
        context = {"timestamp": datetime.now().strftime("%Y%m%d%H%M%S")}
        for key, value in data.items():
            context[key] = self._resolve_text(value, context)
        return context

    def _resolve_payload(self, payload, context: dict):
        if isinstance(payload, dict):
            return {key: self._resolve_payload(value, context) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._resolve_payload(item, context) for item in payload]
        if isinstance(payload, str):
            return self._resolve_text(payload, context)
        return payload

    @staticmethod
    def _resolve_text(template: str, context: dict) -> str:
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            key = match.group(1)
            if key not in context:
                # 这里给出面向测试同事的直白报错，避免把字面量误写成变量引用时难以定位。
                raise KeyError(
                    f"未定义变量：{key}。如果你想输入固定文本，请直接写文本本身，不要加 ${{}}。"
                    f"例如：输入 姓名 张三；只有在引用变量时才写成 ${{patient_name}}。"
                )
            return str(context[key])

        return pattern.sub(replace, template)

    @staticmethod
    def _extract_target(step: dict[str, Any]) -> str:
        for key in ("target", "text", "file_name"):
            if key in step:
                return CaseRunner._stringify_value(step[key])
        return "-"

    @staticmethod
    def _summarize_parameters(step: dict[str, Any]) -> str:
        pairs = []
        for key, value in step.items():
            if key == "target":
                continue
            pairs.append(f"{key}={CaseRunner._stringify_value(value)}")
        return "；".join(pairs) if pairs else "-"

    @staticmethod
    def _stringify_value(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
