from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ASSET_ROOT = Path(__file__).resolve().parent / "assets"
_IGNORED_TEXT_VALUES = {"", "Property does not exist", "None"}

WINDOW_KEY_ALIASES = {
    "窗口标识": "window_id",
    "资产类型": "asset_type",
    "中文名称": "label",
    "所属窗口": "owner_window",
    "AutomationId": "automation_id",
    "ControlType": "control_type",
    "Name": "name",
    "ClassName": "class_name",
    "是否唯一": "unique",
    "锚点元素": "anchors",
    "用途说明": "description",
    "交互标定": "interaction_calibration",
}

ELEMENT_KEY_ALIASES = {
    "元素标识": "element_id",
    "资产类型": "asset_type",
    "中文名称": "label",
    "所属窗口": "window",
    "AutomationId": "automation_id",
    "ControlType": "control_type",
    "Name": "name",
    "ClassName": "class_name",
    "是否唯一": "unique",
    "锚点元素": "anchors",
    "用途说明": "description",
}

ASSERTION_KEY_ALIASES = {
    "断言标识": "assertion_id",
    "中文名称": "label",
    "用途说明": "description",
    "检查项": "checks",
}

CHECK_KEY_ALIASES = {
    "名称": "step_name",
    "动作": "action",
    "窗口": "window",
    "元素": "element",
    "按钮": "button",
    "值": "value",
    "文本": "text",
    "超时": "timeout",
    "参数": "params",
    "可选": "optional",
}

INTERACTION_KEY_ALIASES = {
    "波形左比例": "waveform_left_ratio",
    "波形右比例": "waveform_right_ratio",
    "波形上比例": "waveform_top_ratio",
    "波形下比例": "waveform_bottom_ratio",
    "进度条左比例": "timeline_left_ratio",
    "进度条右比例": "timeline_right_ratio",
    "进度条上比例": "timeline_top_ratio",
    "进度条下比例": "timeline_bottom_ratio",
}


class AssetStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or DEFAULT_ASSET_ROOT
        self.window_dir = self.root_dir / "windows"
        self.element_dir = self.root_dir / "elements"
        self.assertion_dir = self.root_dir / "assertions"
        self._window_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None = None
        self._element_cache: tuple[
            dict[str, dict[str, Any]],
            dict[tuple[str, str], dict[str, Any]],
            dict[str, list[dict[str, Any]]],
        ] | None = None
        self._assertion_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None = None

    def load_windows(self) -> dict[str, dict[str, Any]]:
        by_id, _ = self._load_window_cache()
        return deepcopy(by_id)

    def load_elements(self) -> dict[str, dict[str, Any]]:
        by_id, _, _ = self._load_element_cache()
        return deepcopy(by_id)

    def load_assertions(self) -> dict[str, dict[str, Any]]:
        by_id, _ = self._load_assertion_cache()
        return deepcopy(by_id)

    def resolve_window(self, reference: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(reference, dict):
            return deepcopy(reference)
        by_id, by_label = self._load_window_cache()
        asset = by_id.get(reference) or by_label.get(reference)
        if asset is None:
            raise KeyError(f"未找到正式窗口资产: {reference}")
        return self._build_locator_payload(asset)

    def resolve_element(self, reference: str | dict[str, Any], window: str | None = None) -> dict[str, Any]:
        if isinstance(reference, dict):
            return deepcopy(reference)
        by_id, by_window_label, by_label = self._load_element_cache()
        asset = by_id.get(reference)
        if asset is None and window is not None:
            asset = by_window_label.get((window, reference))
        if asset is None:
            candidates = by_label.get(reference, [])
            if len(candidates) == 1:
                asset = candidates[0]
            elif len(candidates) > 1:
                windows = "、".join(sorted(item["window"] for item in candidates))
                raise KeyError(f"元素 {reference} 在多个窗口下重复出现，请显式指定窗口: {windows}")
        if asset is None:
            raise KeyError(f"未找到正式元素资产: {reference}")
        return self._build_locator_payload(asset)

    def resolve_assertion(self, reference: str) -> dict[str, Any]:
        by_id, by_label = self._load_assertion_cache()
        asset = by_id.get(reference) or by_label.get(reference)
        if asset is None:
            raise KeyError(f"未找到正式断言资产: {reference}")
        return deepcopy(asset)

    def _load_window_cache(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        if self._window_cache is not None:
            return self._window_cache
        by_id: dict[str, dict[str, Any]] = {}
        by_label: dict[str, dict[str, Any]] = {}
        for path in self._iter_yaml_files(self.window_dir):
            for row in self._extract_rows(path, ("窗口资产", "windows")):
                asset = self._normalize_window_asset(row)
                by_id[asset["window_id"]] = asset
                by_label[asset["label"]] = asset
        self._window_cache = (by_id, by_label)
        return self._window_cache

    def _load_element_cache(self):
        if self._element_cache is not None:
            return self._element_cache
        by_id: dict[str, dict[str, Any]] = {}
        by_window_label: dict[tuple[str, str], dict[str, Any]] = {}
        by_label: dict[str, list[dict[str, Any]]] = {}
        for path in self._iter_yaml_files(self.element_dir):
            for row in self._extract_rows(path, ("元素资产", "elements")):
                asset = self._normalize_element_asset(row)
                by_id[asset["element_id"]] = asset
                by_window_label[(asset["window"], asset["label"])] = asset
                by_label.setdefault(asset["label"], []).append(asset)
        self._element_cache = (by_id, by_window_label, by_label)
        return self._element_cache

    def _load_assertion_cache(self) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        if self._assertion_cache is not None:
            return self._assertion_cache
        by_id: dict[str, dict[str, Any]] = {}
        by_label: dict[str, dict[str, Any]] = {}
        for path in self._iter_yaml_files(self.assertion_dir):
            for row in self._extract_rows(path, ("断言资产", "assertions")):
                asset = self._normalize_assertion_asset(row)
                by_id[asset["assertion_id"]] = asset
                by_label[asset["label"]] = asset
        self._assertion_cache = (by_id, by_label)
        return self._assertion_cache

    @staticmethod
    def _iter_yaml_files(directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(directory.rglob("*.yaml"), key=lambda item: item.as_posix())

    @staticmethod
    def _extract_rows(path: Path, container_keys: tuple[str, str]) -> list[dict[str, Any]]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get(container_keys[0]) or payload.get(container_keys[1]) or []
        else:
            raise ValueError(f"资产文件格式不正确: {path}")
        if not isinstance(rows, list):
            raise ValueError(f"资产文件顶层列表结构不正确: {path}")
        return [row for row in rows if isinstance(row, dict)]

    def _normalize_window_asset(self, raw_asset: dict[str, Any]) -> dict[str, Any]:
        asset = {WINDOW_KEY_ALIASES.get(key, key): value for key, value in raw_asset.items()}
        label = self._normalize_scalar(asset.get("label"))
        if not label:
            raise ValueError("正式窗口资产缺少中文名称")
        window_id = self._normalize_scalar(asset.get("window_id")) or self._derive_id("window", label)
        automation_id = self._clean_optional_text(asset.get("automation_id"))
        title = self._clean_optional_text(asset.get("name"))
        if not title and not automation_id:
            title = label
        return {
            "window_id": window_id,
            "asset_type": self._normalize_scalar(asset.get("asset_type")) or "窗口",
            "label": label,
            "owner_window": self._normalize_scalar(asset.get("owner_window")) or label,
            "automation_id": automation_id,
            "control_type": self._normalize_scalar(asset.get("control_type")) or "Window",
            "title": title,
            "class_name": self._clean_optional_text(asset.get("class_name")),
            "unique": self._normalize_bool(asset.get("unique"), default=True),
            "anchors": self._normalize_anchor_values(asset.get("anchors")),
            "description": self._normalize_scalar(asset.get("description")),
            "interaction_calibration": self._normalize_interaction_calibration(asset.get("interaction_calibration")),
        }

    def _normalize_element_asset(self, raw_asset: dict[str, Any]) -> dict[str, Any]:
        asset = {ELEMENT_KEY_ALIASES.get(key, key): value for key, value in raw_asset.items()}
        label = self._normalize_scalar(asset.get("label"))
        window = self._normalize_scalar(asset.get("window"))
        if not label or not window:
            raise ValueError("正式元素资产必须同时提供中文名称和所属窗口")
        element_id = self._normalize_scalar(asset.get("element_id")) or self._derive_id("element", f"{window}_{label}")
        return {
            "element_id": element_id,
            "asset_type": self._normalize_scalar(asset.get("asset_type")) or "元素",
            "label": label,
            "window": window,
            "automation_id": self._clean_optional_text(asset.get("automation_id")),
            "control_type": self._normalize_scalar(asset.get("control_type")),
            "title": self._clean_optional_text(asset.get("name")),
            "class_name": self._clean_optional_text(asset.get("class_name")),
            "unique": self._normalize_bool(asset.get("unique"), default=True),
            "anchors": self._normalize_anchor_values(asset.get("anchors")),
            "description": self._normalize_scalar(asset.get("description")),
        }

    def _normalize_assertion_asset(self, raw_asset: dict[str, Any]) -> dict[str, Any]:
        asset = {ASSERTION_KEY_ALIASES.get(key, key): value for key, value in raw_asset.items()}
        label = self._normalize_scalar(asset.get("label"))
        if not label:
            raise ValueError("正式断言资产缺少中文名称")
        assertion_id = self._normalize_scalar(asset.get("assertion_id")) or self._derive_id("assertion", label)
        checks = asset.get("checks", [])
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"正式断言资产缺少检查项: {label}")
        normalized_checks = [self._normalize_assertion_check(item) for item in checks if isinstance(item, dict)]
        if not normalized_checks:
            raise ValueError(f"正式断言资产检查项格式不正确: {label}")
        return {
            "assertion_id": assertion_id,
            "label": label,
            "description": self._normalize_scalar(asset.get("description")),
            "checks": normalized_checks,
        }

    def _normalize_assertion_check(self, raw_check: dict[str, Any]) -> dict[str, Any]:
        check = {CHECK_KEY_ALIASES.get(key, key): value for key, value in raw_check.items()}
        params = {
            self._normalize_scalar(key): self._normalize_value(value)
            for key, value in (check.get("params") or {}).items()
        }
        return {
            "step_name": self._normalize_scalar(check.get("step_name")),
            "action": self._normalize_scalar(check.get("action")),
            "window": self._normalize_scalar(check.get("window")),
            "element": self._normalize_scalar(check.get("element") or check.get("button")),
            "value": self._normalize_value(check.get("value")),
            "text": self._normalize_scalar(check.get("text")),
            "timeout": self._normalize_scalar(check.get("timeout")),
            "params": params,
            "optional": self._normalize_bool(check.get("optional"), default=False),
        }

    @staticmethod
    def _build_locator_payload(asset: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "label": asset.get("label", ""),
            "automation_id": asset.get("automation_id", ""),
            "control_type": asset.get("control_type", ""),
            "title": asset.get("title", ""),
            "class_name": asset.get("class_name", ""),
            "interaction_calibration": deepcopy(asset.get("interaction_calibration") or {}),
        }
        return {key: value for key, value in payload.items() if value not in ("", None, {})}

    @staticmethod
    def _normalize_anchor_values(value: Any) -> list[str]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [part.strip() for part in value.replace("，", ",").split(",") if part.strip()]
        return [str(value).strip()]

    @staticmethod
    def _normalize_interaction_calibration(value: Any) -> dict[str, float]:
        if value in (None, "", {}):
            return {}
        if not isinstance(value, dict):
            raise ValueError("窗口交互标定必须是字典结构")
        normalized: dict[str, float] = {}
        for key, item in value.items():
            target_key = INTERACTION_KEY_ALIASES.get(str(key).strip(), str(key).strip())
            try:
                normalized[target_key] = float(item)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"窗口交互标定值非法: {key}={item}") from exc
        return normalized

    @staticmethod
    def _normalize_bool(value: Any, default: bool) -> bool:
        if value in (None, ""):
            return default
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y", "是", "开启", "开"}:
            return True
        if normalized in {"0", "false", "no", "n", "否", "关闭", "关"}:
            return False
        return default

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, list):
            return [AssetStore._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): AssetStore._normalize_value(item) for key, item in value.items()}
        return AssetStore._normalize_scalar(value)

    @staticmethod
    def _normalize_scalar(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _clean_optional_text(value: Any) -> str:
        text = AssetStore._normalize_scalar(value)
        return "" if text in _IGNORED_TEXT_VALUES else text

    @staticmethod
    def _derive_id(prefix: str, label: str) -> str:
        return f"{prefix}.{label}"


FormalAssetStore = AssetStore
