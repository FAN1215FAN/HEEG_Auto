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


def load_case_catalog(selected_case_ids: set[str] | None = None) -> list[dict]:
    loader = FormalCaseLoader()
    catalog: list[dict] = []
    for case_file in discover_case_paths():
        payload = loader.load(case_file)
        if selected_case_ids and payload["case_id"] not in selected_case_ids:
            continue
        catalog.append(
            {
                "path": case_file,
                "case_id": payload["case_id"],
                "case_name": payload["case_name"],
                "module_chain_labels": payload.get("module_chain_labels", []),
                "session_policy": payload.get("session_policy", "\u81ea\u52a8"),
                "tags": payload.get("tags", []),
            }
        )
    return catalog


def selected_case_ids_from_env() -> set[str] | None:
    raw = os.environ.get(CASE_FILTER_ENV, "").strip()
    if not raw:
        return None
    return {item.strip() for item in raw.split(",") if item.strip()}


def build_case_params(ui: bool = False):
    params = []
    for item in load_case_catalog(selected_case_ids=selected_case_ids_from_env()):
        module_chain = " -> ".join(item["module_chain_labels"]) or "-"
        display_id = f"{item['case_id']} | {item['case_name']} | \u6a21\u5757\u94fe: {module_chain}"
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
