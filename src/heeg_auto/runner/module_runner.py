from __future__ import annotations

import re
from copy import deepcopy
from time import perf_counter
from typing import Any, Callable

from heeg_auto.elements import ElementStore
from heeg_auto.modules import ModuleStore
from heeg_auto.runner.exceptions import ModuleExecutionError

MODULE_PARAM_ALIASES = {
    "姓名": "patient_name",
    "患者姓名": "patient_name",
    "性别": "gender",
    "利手": "habit_hand",
    "病历号": "patient_id",
    "脑电号": "eeg_id",
    "备注": "note",
    "预期错误包含": "expect_error_contains",
    "设备类型": "device_type",
    "采样率": "sample_rate",
    "波特率": "baud_rate",
    "头盒数目": "head_box_number",
    "IP地址": "ip_address",
    "IP地址1": "ip_address_1",
    "IP地址2": "ip_address_2",
    "端口": "port",
    "设备名称": "device_name",
    "设备增益": "gain_value",
    "软件路径": "exe_path",
    "exe路径": "exe_path",
    "会话模式": "session_mode",
    "变参值": "variant_value",
}

ProgressCallback = Callable[[str], None]


class ModuleRunner:
    def __init__(self) -> None:
        self.module_store = ModuleStore()

    def run_chain(
        self,
        actions,
        element_store: ElementStore,
        module_chain: list[dict],
        progress_callback: ProgressCallback | None = None,
    ) -> list[dict]:
        module_results = []
        for entry in module_chain:
            module_definition = self.module_store.load(entry["module"])
            elements = element_store.load(module_definition["element_module"]) if module_definition.get("element_module") else {}
            module_results.append(
                self._run_module(
                    actions=actions,
                    elements=elements,
                    module_definition=module_definition,
                    params=entry.get("params", {}),
                    assertion_group=entry.get("assertion_group"),
                    progress_callback=progress_callback,
                )
            )
        return module_results

    def _run_module(
        self,
        actions,
        elements: dict[str, dict],
        module_definition: dict[str, Any],
        params: dict[str, Any],
        assertion_group: str | None,
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        step_results: list[dict[str, Any]] = []
        context = self._build_context(params)
        try:
            for step in module_definition.get("steps", []):
                for step_context in self._iter_step_contexts(step, context):
                    self._run_step(actions, elements, step, step_context, step_results, stage="步骤", progress_callback=progress_callback)
            assertions = self._resolve_assertions(module_definition, assertion_group)
            for step in assertions:
                for step_context in self._iter_step_contexts(step, context):
                    self._run_step(actions, elements, step, step_context, step_results, stage="断言", progress_callback=progress_callback)
        except Exception as exc:
            failed_step = step_results[-1]["step_name"] if step_results else ""
            raise ModuleExecutionError(
                module_id=module_definition["module_id"],
                module_label=module_definition["module_label"],
                failed_step=failed_step,
                message=str(exc),
                step_results=step_results,
            ) from exc
        return {
            "module_id": module_definition["module_id"],
            "module_label": module_definition["module_label"],
            "assertion_group": assertion_group or "",
            "status": "PASS",
            "failed_step": "",
            "step_results": step_results,
        }

    @staticmethod
    def _resolve_assertions(module_definition: dict[str, Any], assertion_group: str | None) -> list[dict[str, Any]]:
        assertions = module_definition.get("assertions", {})
        if not assertion_group:
            return []
        if assertion_group not in assertions:
            raise KeyError(f"模块 {module_definition['module_label']} 未定义断言组：{assertion_group}")
        return assertions[assertion_group]

    def _iter_step_contexts(self, step: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
        conditional_key = step.get("when_param")
        if not conditional_key:
            return [context]
        internal_key = MODULE_PARAM_ALIASES.get(conditional_key, conditional_key)
        value = context.get(internal_key)
        if isinstance(value, list):
            contexts = []
            for item in value:
                step_context = deepcopy(context)
                step_context[internal_key] = item
                step_context[conditional_key] = item
                contexts.append(step_context)
            return contexts
        return [context]

    def _run_step(
        self,
        actions,
        elements: dict[str, dict],
        step: dict[str, Any],
        context: dict[str, Any],
        step_results: list[dict[str, Any]],
        stage: str,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        conditional_key = step.get("when_param")
        step_name = step.get("step_name") or step.get("action") or "unnamed_step"
        action_name = step.get("action", "")
        if conditional_key:
            internal_key = MODULE_PARAM_ALIASES.get(conditional_key, conditional_key)
            if not context.get(internal_key):
                step_results.append(
                    {
                        "stage": stage,
                        "step_name": step_name,
                        "action": action_name,
                        "status": "SKIP",
                        "duration_seconds": 0,
                        "error_summary": f"未提供参数：{conditional_key}",
                    }
                )
                return
        if progress_callback:
            progress_callback(f"{stage}:{step_name}:开始")
        started = perf_counter()
        payload = self._build_action_payload(elements, step, context)
        try:
            action_id = actions.resolve_action_name(action_name)
            getattr(actions, action_id)(**payload)
            step_results.append(
                {
                    "stage": stage,
                    "step_name": step_name,
                    "action": action_name,
                    "status": "PASS",
                    "duration_seconds": round(perf_counter() - started, 3),
                    "error_summary": "",
                }
            )
            if progress_callback:
                progress_callback(f"{stage}:{step_name}:完成")
        except Exception as exc:
            if step.get("optional"):
                step_results.append(
                    {
                        "stage": stage,
                        "step_name": step_name,
                        "action": action_name,
                        "status": "SKIP",
                        "duration_seconds": round(perf_counter() - started, 3),
                        "error_summary": str(exc),
                    }
                )
                if progress_callback:
                    progress_callback(f"{stage}:{step_name}:可选跳过")
                return
            step_results.append(
                {
                    "stage": stage,
                    "step_name": step_name,
                    "action": action_name,
                    "status": "FAIL",
                    "duration_seconds": round(perf_counter() - started, 3),
                    "error_summary": str(exc),
                }
            )
            if progress_callback:
                progress_callback(f"{stage}:{step_name}:失败")
            raise

    def _build_action_payload(self, elements: dict[str, dict], step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if step.get("element"):
            payload["target"] = ElementStore.resolve_reference(elements, self._resolve_text(str(step["element"]), context))
        if step.get("value") is not None:
            payload["value"] = self._resolve_payload_value(step["value"], context)
        if step.get("text") is not None:
            payload["text"] = self._resolve_text(str(step["text"]), context)
        if step.get("timeout") is not None:
            payload["timeout"] = int(self._resolve_text(str(step["timeout"]), context))
        if step.get("file_name") is not None:
            payload["file_name"] = self._resolve_text(str(step["file_name"]), context)
        if step.get("exe_path") is not None:
            payload["exe_path"] = self._resolve_text(str(step["exe_path"]), context)
        if step.get("session_mode") is not None:
            payload["session_mode"] = self._resolve_text(str(step["session_mode"]), context)
        return payload

    def _build_context(self, params: dict[str, Any]) -> dict[str, Any]:
        context = dict(params)
        for display_key, internal_key in MODULE_PARAM_ALIASES.items():
            if internal_key in params:
                context[display_key] = params[internal_key]
        return context

    def _resolve_payload_value(self, value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, list):
            return [self._resolve_text(str(item), context) for item in value]
        return self._resolve_text(str(value), context)

    @staticmethod
    def _resolve_text(template: str, context: dict[str, Any]) -> str:
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            raw_key = match.group(1)
            key = MODULE_PARAM_ALIASES.get(raw_key, raw_key)
            if key not in context:
                raise KeyError(f"未定义变量：{raw_key}")
            value = context[key]
            if isinstance(value, list):
                raise TypeError(f"变量 {raw_key} 是列表，不能直接作为单个文本替换。")
            return str(value)

        return pattern.sub(replace, template)
