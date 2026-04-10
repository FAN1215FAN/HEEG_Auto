from __future__ import annotations

import os
from pathlib import Path

import pytest

from heeg_auto.modules import ModuleStore
from heeg_auto.runner.case_resolver import load_case_payload
from heeg_auto.runner.directory_lifecycle import SUPPORT_FILE_NAMES

CASE_ROOT = Path("src/heeg_auto/cases")
CASE_FILTER_ENV = "HEEG_CASE_IDS"
CASE_DIR_FILTER_ENV = "HEEG_CASE_DIRS"
CASE_FILE_FILTER_ENV = "HEEG_CASE_FILE"
KNOWN_DYNAMIC_MARKS = {"smoke", "patient", "device", "start", "v2"}


def discover_case_paths() -> list[Path]:
    return sorted(
        [path for path in CASE_ROOT.rglob("*.yaml") if path.name not in SUPPORT_FILE_NAMES],
        key=lambda path: path.as_posix(),
    )


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


def _normalize_selected_dirs(selected_case_dirs: list[str] | set[str] | None) -> list[str] | None:
    if selected_case_dirs is None:
        return None
    if isinstance(selected_case_dirs, set):
        return sorted(selected_case_dirs)
    ordered: list[str] = []
    seen: set[str] = set()
    for directory in selected_case_dirs:
        if directory not in seen:
            ordered.append(directory)
            seen.add(directory)
    return ordered


def _relative_dir(case_file: Path) -> str:
    relative_parent = case_file.relative_to(CASE_ROOT).parent.as_posix()
    return relative_parent if relative_parent != "." else "根目录"


def _build_plan_label(payload: dict) -> str:
    parts: list[str] = []
    variant = payload.get("variant")
    if variant:
        param_labels = "、".join(item["param_label"] for item in variant.get("params", []))
        unit = "组" if len(variant.get("params", [])) > 1 else "值"
        module_label = variant.get("module_label")
        if module_label:
            parts.append(f"变参: {module_label} / {param_labels} / {len(variant['values'])}{unit}")
        else:
            parts.append(f"变参: {param_labels} / {len(variant['values'])}{unit}")
    if payload.get("loop_count", 1) > 1:
        parts.append(f"循环: {payload['loop_count']}次")
    if payload.get("case_format") == "v2":
        parts.append(f"步骤: {len(payload.get('steps', []))}步")
    return " | ".join(parts)


def _normalize_directory_text(text: str) -> str:
    normalized = text.strip().replace("\\", "/").replace("，", "/")
    return "/".join(part.strip() for part in normalized.split("/") if part.strip())


def _resolve_directory_tokens(tokens: list[str], available_directories: set[str]) -> set[str]:
    segment_map: dict[str, list[str]] = {}
    for directory in available_directories:
        normalized_directory = _normalize_directory_text(directory)
        for segment in [part for part in normalized_directory.split("/") if part]:
            segment_map.setdefault(segment, []).append(directory)
    resolved: set[str] = set()
    for token in tokens:
        normalized_token = _normalize_directory_text(token)
        if not normalized_token:
            continue
        matches = segment_map.get(normalized_token, [])
        if normalized_token in available_directories:
            matches = [normalized_token]
        if len(matches) == 1:
            resolved.add(matches[0])
            continue
        if len(matches) > 1:
            joined = "、".join(sorted(matches))
            raise ValueError(f"文件夹名称匹配到多个目录：{joined}。请改成更具体且唯一的文件夹名称。")
        raise ValueError(f"无效文件夹：{token}。请输入存在的正式 case 目录名称。")
    return resolved


def _dedupe_items_by_case_id(items: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if item["case_id"] in seen:
            continue
        deduped.append(item)
        seen.add(item["case_id"])
    return deduped


def load_case_catalog(
    selected_case_ids: list[str] | set[str] | None = None,
    selected_case_dirs: list[str] | set[str] | None = None,
    selected_case_file: str | None = None,
) -> list[dict]:
    discovered = []
    for case_file in discover_case_paths():
        payload = load_case_payload(case_file)
        discovered.append(
            {
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
                "case_format": payload.get("case_format", "v1"),
            }
        )
    items = sorted(discovered, key=lambda item: (item["relative_dir"], item["case_id"], item["relative_path"]))
    items = _dedupe_items_by_case_id(items)

    if selected_case_file:
        target = Path(selected_case_file)
        target_posix = target.as_posix()
        items = [item for item in items if item["path"].as_posix() == target_posix or item["relative_path"] == target_posix]

    ordered_selected_ids = _normalize_selected_ids(selected_case_ids)
    ordered_selected_dirs = _normalize_selected_dirs(selected_case_dirs)

    if ordered_selected_dirs is not None:
        resolved_dirs = _resolve_directory_tokens(ordered_selected_dirs, {item["relative_dir"] for item in items})
        items = [item for item in items if item["relative_dir"] in resolved_dirs]

    if ordered_selected_ids is not None:
        filtered_by_id = {item["case_id"]: item for item in items}
        items = [filtered_by_id[case_id] for case_id in ordered_selected_ids if case_id in filtered_by_id]

    if (selected_case_file or ordered_selected_ids or ordered_selected_dirs) and not items:
        raise ValueError("筛选后未匹配到任何正式 case。")
    return items


def build_directory_catalog(
    selected_case_ids: list[str] | set[str] | None = None,
    selected_case_dirs: list[str] | set[str] | None = None,
    selected_case_file: str | None = None,
) -> list[dict]:
    directories: dict[str, list[dict]] = {}
    for item in load_case_catalog(
        selected_case_ids=selected_case_ids,
        selected_case_dirs=selected_case_dirs,
        selected_case_file=selected_case_file,
    ):
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


def selected_case_dirs_from_env() -> list[str] | None:
    raw = os.environ.get(CASE_DIR_FILTER_ENV, "").strip()
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def selected_case_file_from_env() -> str | None:
    raw = os.environ.get(CASE_FILE_FILTER_ENV, "").strip()
    return raw or None


def _build_case_display_id(item: dict) -> str:
    module_chain = " -> ".join(item["module_chain_labels"]) or "-"
    display_id = f"{item['case_id']} | {item['case_name']} | 目录: {item['relative_dir']} | 模块链: {module_chain}"
    if item.get("plan_label"):
        display_id = f"{display_id} | {item['plan_label']}"
    return display_id


def _build_case_marks(item: dict, ui: bool = False):
    marks = [getattr(pytest.mark, tag) for tag in item.get("tags", []) if tag in KNOWN_DYNAMIC_MARKS]
    if item.get("case_format") == "v2":
        marks.append(pytest.mark.v2)
    if ui:
        marks.extend([pytest.mark.ui, pytest.mark.formal])
    return marks


def build_case_params(ui: bool = False):
    params = []
    for item in load_case_catalog(
        selected_case_ids=selected_case_ids_from_env(),
        selected_case_dirs=selected_case_dirs_from_env(),
        selected_case_file=selected_case_file_from_env(),
    ):
        params.append(pytest.param(item["path"], id=_build_case_display_id(item), marks=_build_case_marks(item, ui=ui)))
    return params


def build_case_item_params(ui: bool = False):
    params = []
    for item in load_case_catalog(
        selected_case_ids=selected_case_ids_from_env(),
        selected_case_dirs=selected_case_dirs_from_env(),
        selected_case_file=selected_case_file_from_env(),
    ):
        params.append(pytest.param(item, id=_build_case_display_id(item), marks=_build_case_marks(item, ui=ui)))
    return params


def build_module_params():
    module_store = ModuleStore()
    params = []
    for module_id in sorted(module_store.file_registry):
        payload = module_store.load(module_id)
        display_id = f"{payload['module_id']} | {payload['module_label']}"
        params.append(pytest.param(module_id, id=display_id, marks=[pytest.mark.smoke]))
    return params