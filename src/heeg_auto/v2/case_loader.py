from __future__ import annotations

import csv
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from heeg_auto.runner.case_loader import CONTEXT_KEY_ALIASES, PARAM_KEY_ALIASES

CASE_KEY_ALIASES = {
    "用例编号": "case_id",
    "用例名称": "case_name",
    "标签": "tags",
    "数据": "data",
    "参数": "data",
    "变参": "variant",
    "循环次数": "loop_count",
    "失败即停": "stop_on_failure",
    "步骤": "steps",
}

VARIANT_KEY_ALIASES = {
    "参数": "params",
    "候选值": "values",
}

STEP_KEY_ALIASES = {
    "名称": "step_name",
    "窗口": "window",
    "元素": "element",
    "按钮": "button",
    "动作": "action",
    "值": "value",
    "文本": "text",
    "超时": "timeout",
    "参数": "params",
    "断言": "assertions",
    "可选": "optional",
}


class _NoDuplicateSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"YAML 中存在重复键：{key}。同名字段只能保留一份。")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_NoDuplicateSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


class V2CaseLoader:
    def load(self, case_path: str | Path) -> dict[str, Any]:
        case_file = Path(case_path)
        raw_payload = yaml.load(case_file.read_text(encoding="utf-8"), Loader=_NoDuplicateSafeLoader)
        if not isinstance(raw_payload, dict):
            raise ValueError("V2 case 顶层必须是字典结构。")
        payload = self._normalize_case(raw_payload)
        payload["case_path"] = str(case_file)
        payload["context"] = self._build_context(payload.get("data", {}), payload.get("variant"))
        payload["steps"] = self._resolve_payload(payload.get("steps", []), payload["context"])
        return payload

    def _normalize_case(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        payload = {CASE_KEY_ALIASES.get(key, key): value for key, value in raw_payload.items()}
        tags = payload.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        raw_steps = payload.get("steps", [])
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("V2 case 必须包含非空步骤列表。")
        return {
            "case_id": self._normalize_scalar(payload.get("case_id", "")),
            "case_name": self._normalize_scalar(payload.get("case_name", "")),
            "tags": [self._normalize_scalar(tag) for tag in tags if self._normalize_scalar(tag)],
            "data": self._normalize_data(payload.get("data", {})),
            "variant": self._normalize_variant(payload.get("variant")),
            "loop_count": self._normalize_loop_count(payload.get("loop_count", 1)),
            "stop_on_failure": self._normalize_bool(payload.get("stop_on_failure", False)),
            "steps": [self._normalize_step(step) for step in raw_steps],
        }

    def _normalize_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        if raw_data in (None, {}):
            return {}
        if not isinstance(raw_data, dict):
            raise ValueError("V2 case 顶层参数必须是字典结构。")
        normalized = {}
        for key, value in raw_data.items():
            target_key = PARAM_KEY_ALIASES.get(key, CONTEXT_KEY_ALIASES.get(key, key))
            normalized[target_key] = self._normalize_value(value)
        return normalized

    def _normalize_variant(self, raw_variant: dict[str, Any] | None) -> dict[str, Any] | None:
        if raw_variant in (None, {}):
            return None
        if not isinstance(raw_variant, dict):
            raise ValueError("变参必须是字典结构。")
        variant = {VARIANT_KEY_ALIASES.get(key, key): value for key, value in raw_variant.items()}
        param_specs = self._normalize_variant_params(variant.get("params", []))
        values = variant.get("values", [])
        if not param_specs:
            raise ValueError("变参参数定义不能为空。")
        if not isinstance(values, list) or not values:
            raise ValueError("变参候选值必须是非空列表。")
        rows = [self._normalize_variant_row(item, param_specs) for item in values]
        return {"params": param_specs, "values": rows}

    def _normalize_variant_params(self, raw_params: Any) -> list[dict[str, str]]:
        if isinstance(raw_params, list):
            labels = [self._normalize_scalar(item) for item in raw_params]
        elif isinstance(raw_params, str):
            labels = [part.strip() for part in raw_params.replace("，", ",").split(",") if part.strip()]
        else:
            raise ValueError("变参参数定义必须是字符串或列表。")
        return [
            {
                "param": PARAM_KEY_ALIASES.get(label, label),
                "param_label": label,
            }
            for label in labels
            if label
        ]

    def _normalize_variant_row(self, raw_row: Any, param_specs: list[dict[str, str]]) -> dict[str, Any]:
        row_items = self._normalize_variant_row_items(raw_row, expected_size=len(param_specs))
        if len(row_items) != len(param_specs):
            raise ValueError(
                f"变参候选值列数不匹配：期望 {len(param_specs)} 列，实际 {len(row_items)} 列，原始值：{raw_row}"
            )
        mapping: dict[str, str] = {}
        display_values: list[dict[str, str]] = []
        for spec, item in zip(param_specs, row_items, strict=True):
            value = self._normalize_scalar(item)
            mapping[spec["param"]] = value
            display_values.append(
                {
                    "param": spec["param"],
                    "param_label": spec["param_label"],
                    "value": value,
                }
            )
        return {"mapping": mapping, "display_values": display_values}

    def _normalize_variant_row_items(self, raw_row: Any, expected_size: int) -> list[Any]:
        if isinstance(raw_row, list):
            return raw_row
        if isinstance(raw_row, tuple):
            return list(raw_row)
        if isinstance(raw_row, str):
            text = raw_row.strip()
            if expected_size == 1 and not (text.startswith("(") and text.endswith(")")):
                return [text]
            if text.startswith("(") and text.endswith(")"):
                text = text[1:-1]
            reader = csv.reader(StringIO(text), skipinitialspace=True)
            parsed = next(reader, [])
            return [item.strip() for item in parsed]
        return [raw_row]

    def _normalize_step(self, raw_step: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw_step, dict):
            raise ValueError("步骤必须是字典结构。")
        step = {STEP_KEY_ALIASES.get(key, key): value for key, value in raw_step.items()}
        raw_params = step.get("params") or {}
        if not isinstance(raw_params, dict):
            raise ValueError("步骤参数必须是字典结构。")
        has_direct_target = bool(step.get("action") or step.get("element") or step.get("button") or step.get("value") or step.get("text"))
        action_params: dict[str, Any] = {}
        field_params: dict[str, Any] = {}
        if has_direct_target:
            action_params = {
                PARAM_KEY_ALIASES.get(key, key): self._normalize_value(value)
                for key, value in raw_params.items()
            }
        else:
            field_params = {
                self._normalize_scalar(key): self._normalize_value(value)
                for key, value in raw_params.items()
            }
        return {
            "step_name": self._normalize_scalar(step.get("step_name", "")),
            "window": self._normalize_scalar(step.get("window", "")),
            "element": self._normalize_scalar(step.get("element", "")),
            "button": self._normalize_scalar(step.get("button", "")),
            "action": self._normalize_scalar(step.get("action", "")),
            "value": self._normalize_value(step.get("value")),
            "text": self._normalize_scalar(step.get("text", "")),
            "timeout": self._normalize_scalar(step.get("timeout", "")),
            "params": action_params,
            "field_params": field_params,
            "assertions": self._normalize_assertions(step.get("assertions")),
            "optional": self._normalize_bool(step.get("optional", False)),
        }

    def _normalize_assertions(self, raw_assertions: Any) -> list[str]:
        if raw_assertions in (None, "", []):
            return []
        if isinstance(raw_assertions, str):
            return [self._normalize_scalar(raw_assertions)]
        if isinstance(raw_assertions, list):
            return [self._normalize_scalar(item) for item in raw_assertions if self._normalize_scalar(item)]
        raise ValueError("断言定义必须是字符串或列表。")

    def _build_context(self, data: dict[str, Any], variant: dict[str, Any] | None) -> dict[str, Any]:
        context = {
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
            "variant_value": "${变参值}",
            "变参值": "${变参值}",
        }
        if variant:
            for spec in variant.get("params", []):
                placeholder = f"${{{spec['param_label']}}}"
                context[spec["param"]] = placeholder
                context[spec["param_label"]] = placeholder
        for key, value in data.items():
            if isinstance(value, list):
                context[key] = [self._resolve_text(str(item), context) for item in value]
            else:
                context[key] = self._resolve_text(str(value), context)
        return context

    def _resolve_payload(self, payload, context: dict[str, Any]):
        if isinstance(payload, dict):
            return {key: self._resolve_payload(value, context) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._resolve_payload(item, context) for item in payload]
        if isinstance(payload, str):
            return self._resolve_text(payload, context)
        return payload

    @staticmethod
    def _normalize_loop_count(value: Any) -> int:
        try:
            loop_count = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"循环次数必须是正整数，当前值：{value}") from exc
        if loop_count < 1:
            raise ValueError(f"循环次数必须是正整数，当前值：{value}")
        return loop_count

    @staticmethod
    def _normalize_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "是", "开启", "开"}:
            return True
        if normalized in {"false", "0", "no", "n", "否", "关闭", "关"}:
            return False
        raise ValueError(f"布尔字段格式错误，当前值：{value}")

    def _normalize_value(self, value: Any):
        if isinstance(value, list):
            return [self._normalize_scalar(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._normalize_value(item) for key, item in value.items()}
        if value is None:
            return None
        return self._normalize_scalar(value)

    @staticmethod
    def _normalize_scalar(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _resolve_text(template: str, context: dict[str, Any]) -> str:
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            raw_key = match.group(1)
            key = CONTEXT_KEY_ALIASES.get(raw_key, raw_key)
            if key not in context:
                raise KeyError(f"未定义变量：{raw_key}。如果是固定文本，请直接写，不要写成 ${{...}}。")
            value = context[key]
            if isinstance(value, list):
                raise TypeError(f"变量 {raw_key} 是列表，不能直接作为单个文本替换。")
            return str(value)

        return pattern.sub(replace, template)