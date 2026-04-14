from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime
from time import perf_counter
from typing import Any, Callable

from heeg_auto.assets import AssetStore
from heeg_auto.runner.payload_aliases import CONTEXT_KEY_ALIASES, PARAM_KEY_ALIASES

ProgressCallback = Callable[[str], None]

ACTION_ALIASES = {
    "launch_app": "launch_app",
    "启动应用": "launch_app",
    "click": "click",
    "点击": "click",
    "单击": "click",
    "double_click": "double_click",
    "双击": "double_click",
    "right_click": "right_click",
    "右键": "right_click",
    "drag": "drag",
    "拖动": "drag",
    "input_text": "input_text",
    "输入": "input_text",
    "select_combo": "select_combo",
    "下拉选择": "select_combo",
    "select_radio": "select_radio",
    "选择单选": "select_radio",
    "set_checkbox": "set_checkbox",
    "设置复选框": "set_checkbox",
    "wait_for_window": "wait_for_window",
    "等待窗口": "wait_for_window",
    "wait_visible": "wait_visible",
    "等待可见": "wait_visible",
    "assert_exists": "assert_exists",
    "断言存在": "assert_exists",
    "assert_window_closed": "assert_window_closed",
    "断言窗口关闭": "assert_window_closed",
    "assert_text_visible": "assert_text_visible",
    "断言文本可见": "assert_text_visible",
    "assert_text_not_visible": "assert_text_not_visible",
    "断言文本不可见": "assert_text_not_visible",
    "assert_latest_clipped_record": "assert_latest_clipped_record",
    "断言最新剪辑记录": "assert_latest_clipped_record",
    "screenshot": "screenshot",
    "截图": "screenshot",
}

WINDOW_ACTIONS = {"wait_for_window", "assert_window_closed"}


class StepCaseExecutor:
    def __init__(self, asset_store: AssetStore | None = None) -> None:
        self.asset_store = asset_store or AssetStore()

    def run_case(self, actions, case_data: dict[str, Any], progress_callback: ProgressCallback | None = None) -> dict[str, Any]:
        started_at = datetime.now()
        execution_results: list[dict[str, Any]] = []
        halt_reason = ""
        plan = self._build_execution_plan(case_data)
        for execution in plan:
            if halt_reason and case_data.get("stop_on_failure", False):
                execution_results.append(self._build_not_run_execution(execution, halt_reason))
                continue
            result = self._run_execution(actions, case_data, execution, progress_callback=progress_callback)
            execution_results.append(result)
            if result["status"] == "FAIL" and case_data.get("stop_on_failure", False):
                halt_reason = "前一轮执行失败，失败即停已生效。"
        finished_at = datetime.now()
        return self._build_case_result(case_data, started_at, finished_at, execution_results)

    def _run_execution(self, actions, case_data: dict[str, Any], execution: dict[str, Any], progress_callback: ProgressCallback | None = None) -> dict[str, Any]:
        context = self._build_execution_context(case_data, execution)
        steps = self._resolve_payload(deepcopy(case_data["steps"]), context)
        step_results: list[dict[str, Any]] = []
        started_at = datetime.now()
        status = "PASS"
        error_summary = ""
        failure: dict[str, Any] = {}
        for index, step in enumerate(steps, start=1):
            try:
                step_results.append(
                    self._run_step(
                        actions=actions,
                        step=step,
                        context=context,
                        sequence=index,
                        progress_callback=progress_callback,
                    )
                )
            except Exception as exc:
                status = "FAIL"
                error_summary = str(exc) or exc.__class__.__name__
                failure = {"module_id": "步骤式", "failed_step": step.get("step_name") or f"step_{index}"}
                step_results.append(
                    {
                        "sequence": index,
                        "step_name": step.get("step_name") or f"step_{index}",
                        "status": "FAIL",
                        "action": step.get("action", ""),
                        "duration_seconds": 0,
                        "error_summary": error_summary,
                        "assertion_results": [],
                    }
                )
                break
        finished_at = datetime.now()
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
            "step_results": step_results,
            "error_summary": error_summary,
            "failure": failure,
            "artifact_paths": [],
            "parameter_snapshot": [],
        }

    def _run_step(self, actions, step: dict[str, Any], context: dict[str, Any], sequence: int, progress_callback: ProgressCallback | None = None) -> dict[str, Any]:
        step_name = step.get("step_name") or f"step_{sequence}"
        started = perf_counter()
        action_id = ""
        try:
            if self._is_form_fill_step(step):
                action_id = "fill_form"
                self._run_form_fill_step(actions, step, progress_callback=progress_callback)
                self._merge_step_context(context, step)
            elif self._has_primary_action(step):
                action_id = self._resolve_action_id(step)
                payload = self._build_action_payload(step, action_id)
                if progress_callback:
                    progress_callback(f"步骤式执行:{step_name}:开始")
                getattr(actions, action_id)(**payload)
                self._merge_step_context(context, step)
            assertion_results = self._run_step_assertions(actions, step, context=context, progress_callback=progress_callback)
        except Exception:
            if step.get("optional"):
                return {
                    "sequence": sequence,
                    "step_name": step_name,
                    "status": "SKIP",
                    "action": action_id,
                    "duration_seconds": round(perf_counter() - started, 3),
                    "error_summary": "可选步骤执行失败，已跳过。",
                    "assertion_results": [],
                }
            raise
        if progress_callback:
            progress_callback(f"步骤式执行:{step_name}:完成")
        return {
            "sequence": sequence,
            "step_name": step_name,
            "status": "PASS",
            "action": action_id,
            "duration_seconds": round(perf_counter() - started, 3),
            "error_summary": "",
            "assertion_results": assertion_results,
        }

    def _run_form_fill_step(self, actions, step: dict[str, Any], progress_callback: ProgressCallback | None = None) -> None:
        step_name = step.get("step_name") or "填写表单"
        window = step.get("window", "")
        if not window:
            raise ValueError(f"步骤 {step_name} 缺少窗口上下文。")
        for field_label, field_value in step.get("field_params", {}).items():
            action_id, payload = self._build_field_payload(window=window, field_label=field_label, field_value=field_value)
            if progress_callback:
                progress_callback(f"步骤式执行:{step_name}:{field_label}")
            getattr(actions, action_id)(**payload)

    def _build_field_payload(self, window: str, field_label: str, field_value: Any) -> tuple[str, dict[str, Any]]:
        target = self.asset_store.resolve_element(field_label, window=window)
        control_type = str(target.get("control_type", "")).lower()
        if "combo" in control_type:
            return "select_combo", {"target": target, "value": str(field_value)}
        if "radio" in control_type:
            return "select_radio", {"target": target}
        if "check" in control_type:
            return "set_checkbox", {"target": target, "value": field_value}
        if "edit" in control_type or "text" in control_type or "custom" in control_type:
            return "input_text", {"target": target, "value": str(field_value)}
        raise ValueError(f"字段 {field_label} 无法自动推断表单动作，元素类型：{target}")

    def _run_step_assertions(self, actions, step: dict[str, Any], context: dict[str, Any], progress_callback: ProgressCallback | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for assertion_name in step.get("assertions", []):
            assertion_asset = self.asset_store.resolve_assertion(assertion_name)
            checks = self._resolve_payload(deepcopy(assertion_asset.get("checks", [])), context)
            for check in checks:
                action_id = self._resolve_action_alias(check.get("action", ""))
                payload = self._build_action_payload(check, action_id)
                started = perf_counter()
                if progress_callback:
                    progress_callback(f"步骤式断言:{assertion_asset['label']}:开始")
                getattr(actions, action_id)(**payload)
                if progress_callback:
                    progress_callback(f"步骤式断言:{assertion_asset['label']}:完成")
                results.append(
                    {
                        "assertion_id": assertion_asset["assertion_id"],
                        "assertion_label": assertion_asset["label"],
                        "step_name": check.get("step_name") or assertion_asset["label"],
                        "action": action_id,
                        "status": "PASS",
                        "duration_seconds": round(perf_counter() - started, 3),
                    }
                )
        return results

    def _merge_step_context(self, context: dict[str, Any], step: dict[str, Any]) -> None:
        for key, value in step.get("field_params", {}).items():
            context[key] = value
            normalized_key = CONTEXT_KEY_ALIASES.get(key, key)
            context[normalized_key] = value

    def _build_execution_context(self, case_data: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
        context = dict(case_data["context"])
        for item in execution.get("variant_params", []):
            context[item["param"]] = item["value"]
            context[item["param_label"]] = item["value"]
        if len(execution.get("variant_params", [])) == 1:
            only_value = execution["variant_params"][0]["value"]
            context["variant_value"] = only_value
            context["变参值"] = only_value
        return context

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
                        "variant": {"params": variant_params, "index": variant_index, "total": len(variant_rows)} if variant else None,
                        "variant_params": variant_params,
                    }
                )
                sequence += 1
        return plan

    @staticmethod
    def _is_form_fill_step(step: dict[str, Any]) -> bool:
        return bool(step.get("field_params")) and not (step.get("action") or step.get("element") or step.get("button"))

    @staticmethod
    def _has_primary_action(step: dict[str, Any]) -> bool:
        return bool(step.get("action") or step.get("element") or step.get("button") or step.get("window"))

    def _resolve_action_id(self, step: dict[str, Any]) -> str:
        explicit_action = step.get("action", "")
        if explicit_action:
            return self._resolve_action_alias(explicit_action)
        element_reference = self._step_target_reference(step)
        if element_reference:
            element_asset = self.asset_store.resolve_element(element_reference, window=step.get("window"))
            control_type = str(element_asset.get("control_type", "")).lower()
            if step.get("value") not in (None, ""):
                if "combo" in control_type:
                    return "select_combo"
                if "check" in control_type:
                    return "set_checkbox"
                if "edit" in control_type or "text" in control_type or "custom" in control_type:
                    return "input_text"
            if "radio" in control_type:
                return "select_radio"
            if "button" in control_type:
                return "click"
            return "click"
        if step.get("window"):
            return "wait_for_window"
        raise ValueError(f"步骤 {step.get('step_name', '')} 无法推断执行动作。")

    @staticmethod
    def _resolve_action_alias(action_name: str) -> str:
        if action_name not in ACTION_ALIASES:
            raise KeyError(f"未注册的步骤式动作: {action_name}")
        return ACTION_ALIASES[action_name]

    def _build_action_payload(self, step: dict[str, Any], action_id: str) -> dict[str, Any]:
        payload = self._normalize_action_params(step.get("params", {}))
        if step.get("value") not in (None, ""):
            payload["value"] = step["value"]
        if step.get("text"):
            payload["text"] = step["text"]
        if step.get("timeout"):
            payload["timeout"] = int(str(step["timeout"]))
        if step.get("window"):
            payload["window"] = self.asset_store.resolve_window(step["window"])
        target = self._resolve_target(step, action_id)
        if target:
            payload["target"] = target
        return payload

    @staticmethod
    def _normalize_action_params(raw_params: dict[str, Any] | None) -> dict[str, Any]:
        if not raw_params:
            return {}
        return {
            PARAM_KEY_ALIASES.get(str(key).strip(), str(key).strip()): value
            for key, value in raw_params.items()
        }

    def _resolve_target(self, step: dict[str, Any], action_id: str) -> dict[str, Any] | None:
        element_reference = self._step_target_reference(step)
        if element_reference:
            return self.asset_store.resolve_element(element_reference, window=step.get("window"))
        if step.get("window") and action_id in WINDOW_ACTIONS:
            return self.asset_store.resolve_window(step["window"])
        return None

    @staticmethod
    def _step_target_reference(step: dict[str, Any]) -> str:
        return str(step.get("element") or step.get("button") or "")

    def _resolve_payload(self, payload, context: dict[str, Any]):
        if isinstance(payload, dict):
            return {key: self._resolve_payload(value, context) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._resolve_payload(item, context) for item in payload]
        if isinstance(payload, str):
            return self._resolve_text(payload, context)
        return payload

    @staticmethod
    def _resolve_text(template: str, context: dict[str, Any]) -> str:
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
            "step_results": [],
            "error_summary": reason,
            "failure": {},
            "artifact_paths": [],
            "parameter_snapshot": [],
        }

    @staticmethod
    def _build_case_result(case_data: dict[str, Any], started_at: datetime, finished_at: datetime, execution_results: list[dict[str, Any]]) -> dict[str, Any]:
        first_failure = next((item for item in execution_results if item["status"] == "FAIL"), None)
        passed_runs = sum(1 for item in execution_results if item["status"] == "PASS")
        failed_runs = sum(1 for item in execution_results if item["status"] == "FAIL")
        not_run_runs = sum(1 for item in execution_results if item["status"] == "NOT_RUN")
        status = "FAIL" if failed_runs else "PASS"
        return {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "tags": case_data.get("tags", []),
            "variant": case_data.get("variant"),
            "loop_count": case_data.get("loop_count", 1),
            "stop_on_failure": case_data.get("stop_on_failure", False),
            "passed": status == "PASS",
            "status": status,
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "execution_results": execution_results,
            "summary": {
                "planned_runs": len(execution_results),
                "executed_runs": passed_runs + failed_runs,
                "passed_runs": passed_runs,
                "failed_runs": failed_runs,
                "interrupted_runs": 0,
                "not_run_runs": not_run_runs,
            },
            "error_summary": first_failure["error_summary"] if first_failure else "",
            "artifact_paths": [],
        }
