from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from heeg_auto.runner.case_loader import FormalCaseLoader
from heeg_auto.v2.case_loader import V2CaseLoader


def _read_case_root(case_path: str | Path) -> dict[str, Any]:
    path = Path(case_path)
    payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    if not isinstance(payload, dict):
        raise ValueError(f'正式 case 顶层必须是字典结构：{path}')
    return payload


def detect_case_format(case_path: str | Path) -> str:
    payload = _read_case_root(case_path)
    if '步骤' in payload or 'steps' in payload:
        return 'v2'
    return 'v1'


def load_case_payload(case_path: str | Path) -> dict[str, Any]:
    case_format = detect_case_format(case_path)
    if case_format == 'v2':
        payload = V2CaseLoader().load(case_path)
        payload.setdefault('module_chain_labels', ['V2步骤式'])
    else:
        payload = FormalCaseLoader().load(case_path)
    payload['case_format'] = case_format
    return payload
