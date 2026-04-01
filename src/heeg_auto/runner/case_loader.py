from __future__ import annotations

import re
from datetime import datetime
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
    "会话策略": "session_policy",
    "模块链": "module_chain",
}
MODULE_ENTRY_KEY_ALIASES = {
    "模块": "module",
    "参数": "params",
}
PARAM_KEY_ALIASES = {
    "姓名": "patient_name",
    "患者姓名": "patient_name",
    "性别": "gender",
    "利手": "habit_hand",
    "病历号": "patient_id",
    "脑电号": "eeg_id",
    "备注": "note",
    "预期状态": "expect_status",
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
CONTEXT_KEY_ALIASES = dict(PARAM_KEY_ALIASES)


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
        payload = self._normalize_case(raw_payload)
        context = self._build_context(payload.get("data", {}))
        payload["case_path"] = str(case_file)
        payload["context"] = context
        payload["module_chain"] = self._resolve_payload(payload.get("module_chain", []), context)
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
            "case_id": payload.get("case_id", ""),
            "case_name": payload.get("case_name", ""),
            "tags": tags,
            "data": self._normalize_data(payload.get("data", {})),
            "module_chain": [self._normalize_module_entry(entry) for entry in raw_chain],
        }

    def _normalize_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        normalized = {}
        for key, value in raw_data.items():
            normalized[PARAM_KEY_ALIASES.get(key, CONTEXT_KEY_ALIASES.get(key, key))] = value
        return normalized

    def _normalize_module_entry(self, raw_entry: dict[str, Any]) -> dict[str, Any]:
        entry = {MODULE_ENTRY_KEY_ALIASES.get(key, key): value for key, value in raw_entry.items()}
        params = {
            PARAM_KEY_ALIASES.get(key, key): value
            for key, value in entry.get("params", {}).items()
        }
        return {
            "module": MODULE_NAME_ALIASES.get(entry.get("module", ""), entry.get("module", "")),
            "params": params,
        }

    def _build_context(self, data: dict[str, Any]) -> dict[str, Any]:
        context = {"timestamp": datetime.now().strftime("%Y%m%d%H%M%S")}
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