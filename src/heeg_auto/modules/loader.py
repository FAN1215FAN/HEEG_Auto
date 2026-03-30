from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from heeg_auto.modules.registry import MODULE_FILE_REGISTRY

MODULE_KEY_ALIASES = {
    "模块标识": "module_id",
    "模块名称": "module_label",
    "元素清单": "element_module",
    "参数说明": "parameter_definitions",
    "步骤": "steps",
    "断言": "assertions",
}

STEP_KEY_ALIASES = {
    "名称": "step_name",
    "动作": "action",
    "元素": "element",
    "值": "value",
    "文本": "text",
    "超时": "timeout",
    "文件名": "file_name",
    "可选": "optional",
}


class ModuleStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir
        self.file_registry = MODULE_FILE_REGISTRY

    def load(self, module_id: str) -> dict:
        if module_id not in self.file_registry:
            raise KeyError(f"未注册模块定义：{module_id}")

        payload = yaml.safe_load(self.file_registry[module_id].read_text(encoding="utf-8"))
        normalized = {MODULE_KEY_ALIASES.get(key, key): value for key, value in payload.items()}
        return {
            "module_id": normalized.get("module_id", module_id),
            "module_label": normalized.get("module_label", module_id),
            "element_module": normalized.get("element_module", module_id),
            "parameter_definitions": list(normalized.get("parameter_definitions", [])),
            "steps": [self._normalize_step(step) for step in normalized.get("steps", [])],
            "assertions": {
                status: [self._normalize_step(step) for step in steps]
                for status, steps in normalized.get("assertions", {}).items()
            },
        }

    @staticmethod
    def _normalize_step(step: dict) -> dict:
        return deepcopy({STEP_KEY_ALIASES.get(key, key): value for key, value in step.items()})