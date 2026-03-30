from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml


class ElementStore:
    """元素仓库：支持按内部 key 或中文显示名解析元素。"""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.file_registry = {
            "patient.create": self.root_dir / "patient" / "create_patient.yaml",
        }

    def load(self, module_id: str) -> dict[str, dict]:
        if module_id not in self.file_registry:
            raise KeyError(f"未注册元素清单：{module_id}")

        payload = yaml.safe_load(self.file_registry[module_id].read_text(encoding="utf-8"))
        items = payload.get("items", {})
        if not items:
            raise ValueError(f"元素清单为空：{module_id}")
        return deepcopy(items)

    @staticmethod
    def resolve_reference(elements: dict[str, dict], reference: str | dict) -> dict:
        if isinstance(reference, dict):
            return deepcopy(reference)
        if reference in elements:
            return deepcopy(elements[reference])
        for locator in elements.values():
            if locator.get("label") == reference:
                return deepcopy(locator)
        raise KeyError(f"未找到元素定义：{reference}")