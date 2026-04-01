from __future__ import annotations

import os
from pathlib import Path

import pytest

from heeg_auto.modules import ModuleStore
from heeg_auto.runner.case_loader import FormalCaseLoader

CASE_ROOT = Path("src/heeg_auto/cases")
CASE_FILTER_ENV = "HEEG_CASE_IDS"


def discover_case_paths() -> list[Path]:
    return sorted(CASE_ROOT.rglob("TC_*.yaml"))


def _normalize_selected_ids(selected_case_ids: list[str] | set[str] | None) -> list[str] | None:
    if selected_case_ids is None:
        return None
    if isinstance(selected_case_ids, set):
        return sorted(selected_case_ids)
    ordered: list[str] = []
    seen: set[str] = set()
    for case_id in selected_case_ids:
        if case_id not in seen:
            ordered.append(case_id)
            seen.add(case_id)
    return ordered


def load_case_catalog(selected_case_ids: list[str] | set[str] | None = None) -> list[dict]:
    loader = FormalCaseLoader()
    discovered = []
    by_id: dict[str, dict] = {}
    for case_file in discover_case_paths():
        payload = loader.load(case_file)
        item = {
            "path": case_file,
            "case_id": payload["case_id"],
            "case_name": payload["case_name"],
            "module_chain_labels": payload.get("module_chain_labels", []),
            "tags": payload.get("tags", []),
        }
        discovered.append(item)
        by_id[item["case_id"]] = item
    ordered_selected = _normalize_selected_ids(selected_case_ids)
    if ordered_selected is None:
        return discovered
    return [by_id[case_id] for case_id in ordered_selected if case_id in by_id]


def selected_case_ids_from_env() -> list[str] | None:
    raw = os.environ.get(CASE_FILTER_ENV, "").strip()
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_case_params(ui: bool = False):
    params = []
    for item in load_case_catalog(selected_case_ids=selected_case_ids_from_env()):
        module_chain = " -> ".join(item["module_chain_labels"]) or "-"
        display_id = f"{item['case_id']} | {item['case_name']} | 模块链: {module_chain}"
        marks = [getattr(pytest.mark, tag) for tag in item.get("tags", []) if hasattr(pytest.mark, tag)]
        if ui:
            marks.append(pytest.mark.ui)
        params.append(pytest.param(item["path"], id=display_id, marks=marks))
    return params


def build_module_params():
    module_store = ModuleStore()
    params = []
    for module_id in sorted(module_store.file_registry):
        payload = module_store.load(module_id)
        display_id = f"{payload['module_id']} | {payload['module_label']}"
        params.append(pytest.param(module_id, id=display_id, marks=[pytest.mark.smoke]))
    return params