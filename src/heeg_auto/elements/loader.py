from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

ELEMENT_FILE_REGISTRY = {
    "patient.create": Path("patient") / "create_patient.yaml",
    "device.settings": Path("device") / "device_settings.yaml",
}


class ElementStore:
    """元素仓库：支持按内部 key、显示名称或别名解析元素。"""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.file_registry = {
            module_id: self.root_dir / relative_path
            for module_id, relative_path in ELEMENT_FILE_REGISTRY.items()
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
            if reference in locator.get("aliases", []):
                return deepcopy(locator)
        raise KeyError(f"未找到元素定义：{reference}")
