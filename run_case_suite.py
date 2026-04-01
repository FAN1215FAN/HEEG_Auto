from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from tests.support.case_catalog import CASE_FILTER_ENV, load_case_catalog


def _print_case_catalog(catalog: list[dict]) -> None:
    print("\n可运行的正式 case 列表：")
    for index, item in enumerate(catalog, start=1):
        modules = " -> ".join(item["module_chain_labels"]) or "-"
        print(f"  {index}. {item['case_id']} | {item['case_name']} | 模块链: {modules}")


def _resolve_selection(catalog: list[dict], raw: str) -> list[dict]:
    raw = raw.strip()
    if not raw or raw.lower() in {"all", "a", "全部"}:
        return catalog
    by_index = {str(index): item for index, item in enumerate(catalog, start=1)}
    by_case_id = {item["case_id"]: item for item in catalog}
    selected: list[dict] = []
    seen: set[str] = set()
    for token in [part.strip() for part in raw.split(",") if part.strip()]:
        item = by_index.get(token) or by_case_id.get(token)
        if item is None:
            raise ValueError(f"无效选择：{token}")
        if item["case_id"] not in seen:
            selected.append(item)
            seen.add(item["case_id"])
    if not selected:
        raise ValueError("至少选择一条 case。")
    return selected


def main() -> int:
    catalog = load_case_catalog()
    if not catalog:
        print("未发现任何正式 case。")
        return 1
    _print_case_catalog(catalog)
    print("\n输入 all / 全部 可运行所有 case；也可输入序号或 case 编号，多个用逗号分隔。")
    raw = input("请选择要运行的 case：").strip()
    try:
        selected = _resolve_selection(catalog, raw)
    except ValueError as exc:
        print(str(exc))
        return 1
    selected_ids = ",".join(item["case_id"] for item in selected)
    print("\n本次将运行：")
    for item in selected:
        modules = " -> ".join(item["module_chain_labels"]) or "-"
        print(f"- {item['case_id']} | {item['case_name']} | 模块链: {modules}")
    os.environ[CASE_FILTER_ENV] = selected_ids
    try:
        return pytest.main(["-m", "ui", "--run-ui", "tests/smoke/test_patient_ui_flow.py", "-q"])
    finally:
        os.environ.pop(CASE_FILTER_ENV, None)


if __name__ == "__main__":
    raise SystemExit(main())