from __future__ import annotations

import csv
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import yaml

from heeg_auto.modules import ModuleStore
from heeg_auto.modules.registry import MODULE_NAME_ALIASES

CASE_KEY_ALIASES = {
    "用例编号": "case_id",
    "用例名称": "case_name",
    "标签": "tags",
    "数据": "data",
    "变参": "variant",
    "循环次数": "loop_count",
    "失败即停": "stop_on_failure",
    "会话策略": "session_policy",
    "模块链": "module_chain",
}
MODULE_ENTRY_KEY_ALIASES = {
    "模块": "module",
    "参数": "params",
    "断言组": "assertion_group",
}
VARIANT_KEY_ALIASES = {
    "模块": "module",
    "参数": "params",
    "候选值": "values",
}
PARAM_KEY_ALIASES = {
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
}
CONTEXT_KEY_ALIASES = {
    **PARAM_KEY_ALIASES,
    "变参值": "variant_value",
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


class FormalCaseLoader:
    def __init__(self) -> None:
        self.module_store = ModuleStore()

    def load(self, case_path: str | Path) -> dict[str, Any]:
        case_file = Path(case_path)
        raw_payload = yaml.load(case_file.read_text(encoding="utf-8"), Loader=_NoDuplicateSafeLoader)
        if not isinstance(raw_payload, dict):
            raise ValueError("正式 case 顶层必须是字典结构。")
        payload = self._normalize_case(raw_payload)
        context = self._build_context(payload.get("data", {}), payload.get("variant"))
        payload["case_path"] = str(case_file)
        payload["context"] = context
        payload["module_chain"] = self._resolve_payload(payload.get("module_chain", []), context)
        self._validate_variant(payload.get("variant"), payload["module_chain"])
        payload["module_chain_labels"] = [
            self.module_store.load(entry["module"])["module_label"] for entry in payload["module_chain"]
        ]
        return payload

    def _normalize_case(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        payload = {CASE_KEY_ALIASES.get(key, key): value for key, value in raw_payload.items()}
        tags = payload.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        raw_chain = payload.get("module_chain", [])
        if not isinstance(raw_chain, list):
            raise ValueError("模块链必须是列表结构，请检查是否漏写 '-'。")
        return {
            "case_id": self._normalize_scalar(payload.get("case_id", "")),
            "case_name": self._normalize_scalar(payload.get("case_name", "")),
            "tags": [self._normalize_scalar(tag) for tag in tags],
            "data": self._normalize_data(payload.get("data", {})),
            "variant": self._normalize_variant(payload.get("variant")),
            "loop_count": self._normalize_loop_count(payload.get("loop_count", 1)),
            "stop_on_failure": self._normalize_stop_on_failure(payload.get("stop_on_failure", False)),
            "module_chain": [self._normalize_module_entry(entry) for entry in raw_chain],
        }

    def _normalize_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        normalized = {}
        for key, value in raw_data.items():
            normalized[PARAM_KEY_ALIASES.get(key, CONTEXT_KEY_ALIASES.get(key, key))] = self._normalize_value(value)
        return normalized

    def _normalize_variant(self, raw_variant: dict[str, Any] | None) -> dict[str, Any] | None:
        if raw_variant in (None, {}):
            return None
        if not isinstance(raw_variant, dict):
            raise ValueError("变参必须是字典结构。")
        variant = {VARIANT_KEY_ALIASES.get(key, key): value for key, value in raw_variant.items()}
        module_name = self._normalize_scalar(variant.get("module", ""))
        param_specs = self._normalize_variant_params(variant.get("params", []))
        values = variant.get("values", [])
        if not module_name or not param_specs:
            raise ValueError("变参必须同时提供 模块 和 参数。")
        if not isinstance(values, list) or not values:
            raise ValueError("变参候选值必须是非空列表。")
        rows = [self._normalize_variant_row(item, param_specs) for item in values]
        normalized = {
            "module": MODULE_NAME_ALIASES.get(module_name, module_name),
            "module_label": module_name,
            "params": param_specs,
            "values": rows,
        }
        if len(param_specs) == 1:
            normalized["param"] = param_specs[0]["param"]
            normalized["param_label"] = param_specs[0]["param_label"]
        return normalized

    def _normalize_variant_params(self, raw_params: Any) -> list[dict[str, str]]:
        if isinstance(raw_params, list):
            labels = [self._normalize_scalar(item) for item in raw_params]
        elif isinstance(raw_params, str):
            labels = [part.strip() for part in raw_params.replace("，", ",").split(",") if part.strip()]
        else:
            raise ValueError("变参参数定义必须是字符串或列表。")
        if not labels:
            raise ValueError("变参参数定义不能为空。")
        return [
            {
                "param": PARAM_KEY_ALIASES.get(label, label),
                "param_label": label,
            }
            for label in labels
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
        return {
            "mapping": mapping,
            "display_values": display_values,
        }

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

    def _normalize_module_entry(self, raw_entry: dict[str, Any]) -> dict[str, Any]:
        entry = {MODULE_ENTRY_KEY_ALIASES.get(key, key): value for key, value in raw_entry.items()}
        params = {
            PARAM_KEY_ALIASES.get(key, key): self._normalize_value(value)
            for key, value in entry.get("params", {}).items()
        }
        assertion_group = entry.get("assertion_group")
        if assertion_group is not None:
            assertion_group = self._normalize_scalar(assertion_group)
        return {
            "module": MODULE_NAME_ALIASES.get(entry.get("module", ""), entry.get("module", "")),
            "params": params,
            "assertion_group": assertion_group,
        }

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

    def _validate_variant(self, variant: dict[str, Any] | None, module_chain: list[dict[str, Any]]) -> None:
        if not variant:
            return
        matching_entry = next((entry for entry in module_chain if entry["module"] == variant["module"]), None)
        if matching_entry is None:
            raise ValueError(f"变参目标模块未出现在模块链中：{variant['module_label']}")
        for spec in variant.get("params", []):
            if spec["param"] not in matching_entry.get("params", {}):
                raise ValueError(
                    f"变参目标参数未出现在模块参数中：{variant['module_label']} -> {spec['param_label']}"
                )

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
    def _normalize_stop_on_failure(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "是", "开启", "开"}:
            return True
        if normalized in {"false", "0", "no", "n", "否", "关闭", "关"}:
            return False
        raise ValueError(f"失败即停必须是布尔值，当前值：{value}")

    def _normalize_value(self, value: Any):
        if isinstance(value, list):
            return [self._normalize_scalar(item) for item in value]
        if isinstance(value, dict):
            return {key: self._normalize_value(item) for key, item in value.items()}
        return self._normalize_scalar(value)

    @staticmethod
    def _normalize_scalar(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

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
