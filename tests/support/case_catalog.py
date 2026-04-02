from __future__ import annotations

import os
from pathlib import Path

import pytest

from heeg_auto.modules import ModuleStore
from heeg_auto.runner.case_loader import FormalCaseLoader

CASE_ROOT = Path("src/heeg_auto/cases")
CASE_FILTER_ENV = "HEEG_CASE_IDS"


def discover_case_paths() -> list[Path]:
    return sorted(CASE_ROOT.rglob("*.yaml"), key=lambda path: path.as_posix())


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


def _relative_dir(case_file: Path) -> str:
    relative_parent = case_file.relative_to(CASE_ROOT).parent.as_posix()
    return relative_parent if relative_parent != "." else "根目录"


def _build_plan_label(payload: dict) -> str:
    parts: list[str] = []
    variant = payload.get("variant")
    if variant:
        parts.append(f"变参: {variant['module_label']} / {variant['param_label']} / {len(variant['values'])}值")
    if payload.get("loop_count", 1) > 1:
        parts.append(f"循环: {payload['loop_count']}次")
    return "；".join(parts)


def load_case_catalog(selected_case_ids: list[str] | set[str] | None = None) -> list[dict]:
    loader = FormalCaseLoader()
    discovered = []
    by_id: dict[str, dict] = {}
    for case_file in discover_case_paths():
        payload = loader.load(case_file)
        item = {
            "path": case_file,
            "relative_path": case_file.relative_to(CASE_ROOT).as_posix(),
            "relative_dir": _relative_dir(case_file),
            "file_name": case_file.name,
            "case_id": payload["case_id"],
            "case_name": payload["case_name"],
            "module_chain_labels": payload.get("module_chain_labels", []),
            "tags": payload.get("tags", []),
            "variant": payload.get("variant"),
            "loop_count": payload.get("loop_count", 1),
            "plan_label": _build_plan_label(payload),
        }
        discovered.append(item)
        by_id[item["case_id"]] = item
    discovered = sorted(discovered, key=lambda item: (item["relative_dir"], item["case_id"]))
    ordered_selected = _normalize_selected_ids(selected_case_ids)
    if ordered_selected is None:
        return discovered
    return [by_id[case_id] for case_id in ordered_selected if case_id in by_id]


def build_directory_catalog(selected_case_ids: list[str] | set[str] | None = None) -> list[dict]:
    directories: dict[str, list[dict]] = {}
    for item in load_case_catalog(selected_case_ids=selected_case_ids):
        directories.setdefault(item["relative_dir"], []).append(item)
    return [
        {
            "directory": key,
            "count": len(items),
            "case_ids": [item["case_id"] for item in items],
            "case_names": [item["case_name"] for item in items],
        }
        for key, items in sorted(directories.items())
    ]


def selected_case_ids_from_env() -> list[str] | None:
    raw = os.environ.get(CASE_FILTER_ENV, "").strip()
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_case_params(ui: bool = False):
    params = []
    for item in load_case_catalog(selected_case_ids=selected_case_ids_from_env()):
        module_chain = " -> ".join(item["module_chain_labels"]) or "-"
        display_id = f"{item['case_id']} | {item['case_name']} | 目录: {item['relative_dir']} | 模块链: {module_chain}"
        if item.get("plan_label"):
            display_id = f"{display_id} | {item['plan_label']}"
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
