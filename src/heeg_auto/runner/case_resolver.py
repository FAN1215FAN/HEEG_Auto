from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from heeg_auto.runner.step_case_loader import StepCaseLoader


def _read_case_root(case_path: str | Path) -> dict[str, Any]:
    path = Path(case_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"正式 case 顶层必须是字典结构：{path}")
    return payload


def detect_case_format(case_path: str | Path) -> str:
    payload = _read_case_root(case_path)
    if "步骤" in payload or "steps" in payload:
        return "step"
    raise ValueError(f"当前项目只支持步骤式 case：{Path(case_path)}")


def load_case_payload(case_path: str | Path) -> dict[str, Any]:
    detect_case_format(case_path)
    payload = StepCaseLoader().load(case_path)
    payload.setdefault("module_chain_labels", ["步骤式"])
    payload["case_format"] = "step"
    return payload
