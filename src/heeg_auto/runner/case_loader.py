from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from heeg_auto.modules import ModuleStore
from heeg_auto.modules.registry import MODULE_NAME_ALIASES

CASE_KEY_ALIASES = {
    "\u7528\u4f8b\u7f16\u53f7": "case_id",
    "\u7528\u4f8b\u540d\u79f0": "case_name",
    "\u6807\u7b7e": "tags",
    "\u6570\u636e": "data",
    "\u4f1a\u8bdd\u7b56\u7565": "session_policy",
    "\u6a21\u5757\u94fe": "module_chain",
}

MODULE_ENTRY_KEY_ALIASES = {
    "\u6a21\u5757": "module",
    "\u53c2\u6570": "params",
}

PARAM_KEY_ALIASES = {
    "\u59d3\u540d": "name",
    "\u60a3\u8005\u59d3\u540d": "patient_name",
    "\u6027\u522b": "gender",
    "\u5229\u624b": "habit_hand",
    "\u75c5\u5386\u53f7": "patient_id",
    "\u8111\u7535\u53f7": "eeg_id",
    "\u5907\u6ce8": "note",
    "\u9884\u671f\u72b6\u6001": "expect_status",
    "\u9884\u671f\u9519\u8bef\u5305\u542b": "expect_error_contains",
}

CONTEXT_KEY_ALIASES = {
    "\u60a3\u8005\u59d3\u540d": "patient_name",
    "\u75c5\u5386\u53f7": "patient_id",
    "\u8111\u7535\u53f7": "eeg_id",
}


class FormalCaseLoader:
    def __init__(self) -> None:
        self.module_store = ModuleStore()

    def load(self, case_path: str | Path) -> dict[str, Any]:
        case_file = Path(case_path)
        raw_payload = yaml.safe_load(case_file.read_text(encoding="utf-8"))
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
        return {
            "case_id": payload.get("case_id", ""),
            "case_name": payload.get("case_name", ""),
            "tags": tags,
            "session_policy": payload.get("session_policy", "\u81ea\u52a8"),
            "data": self._normalize_data(payload.get("data", {})),
            "module_chain": [self._normalize_module_entry(entry) for entry in payload.get("module_chain", [])],
        }

    def _normalize_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        normalized = {}
        for key, value in raw_data.items():
            normalized_key = PARAM_KEY_ALIASES.get(key, CONTEXT_KEY_ALIASES.get(key, key))
            normalized[normalized_key] = value
        return normalized

    def _normalize_module_entry(self, raw_entry: dict[str, Any]) -> dict[str, Any]:
        entry = {MODULE_ENTRY_KEY_ALIASES.get(key, key): value for key, value in raw_entry.items()}
        module_name = entry.get("module", "")
        params = {
            PARAM_KEY_ALIASES.get(key, key): value
            for key, value in entry.get("params", {}).items()
        }
        return {
            "module": MODULE_NAME_ALIASES.get(module_name, module_name),
            "params": params,
        }

    def _build_context(self, data: dict[str, Any]) -> dict[str, Any]:
        context = {"timestamp": datetime.now().strftime("%Y%m%d%H%M%S")}
        for key, value in data.items():
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
                raise KeyError(f"\u672a\u5b9a\u4e49\u53d8\u91cf\uff1a{raw_key}")
            return str(context[key])

        return pattern.sub(replace, template)
