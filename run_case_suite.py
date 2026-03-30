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
    print("\n\u53ef\u8fd0\u884c\u7684\u6b63\u5f0f case \u5217\u8868\uff1a")
    for index, item in enumerate(catalog, start=1):
        modules = " -> ".join(item["module_chain_labels"]) or "-"
        print(
            f"  {index}. {item['case_id']} | {item['case_name']} | \u6a21\u5757\u94fe: {modules} | \u4f1a\u8bdd\u7b56\u7565: {item['session_policy']}"
        )


def _resolve_selection(catalog: list[dict], raw: str) -> list[dict]:
    raw = raw.strip()
    if not raw or raw.lower() in {"all", "a", "\u5168\u90e8"}:
        return catalog

    by_index = {str(index): item for index, item in enumerate(catalog, start=1)}
    by_case_id = {item["case_id"]: item for item in catalog}
    selected: list[dict] = []
    seen: set[str] = set()

    for token in [part.strip() for part in raw.split(",") if part.strip()]:
        item = by_index.get(token) or by_case_id.get(token)
        if item is None:
            raise ValueError(f"\u65e0\u6548\u9009\u62e9\uff1a{token}")
        if item["case_id"] not in seen:
            selected.append(item)
            seen.add(item["case_id"])

    if not selected:
        raise ValueError("\u81f3\u5c11\u9009\u62e9\u4e00\u6761 case\u3002")
    return selected


def main() -> int:
    catalog = load_case_catalog()
    if not catalog:
        print("\u672a\u53d1\u73b0\u4efb\u4f55\u6b63\u5f0f case\u3002")
        return 1

    _print_case_catalog(catalog)
    print("\n\u8f93\u5165 all / \u5168\u90e8 \u53ef\u8fd0\u884c\u6240\u6709 case\uff1b\u4e5f\u53ef\u8f93\u5165\u5e8f\u53f7\u6216 case \u7f16\u53f7\uff0c\u591a\u4e2a\u7528\u9017\u53f7\u5206\u9694\u3002")
    raw = input("\u8bf7\u9009\u62e9\u8981\u8fd0\u884c\u7684 case\uff1a").strip()

    try:
        selected = _resolve_selection(catalog, raw)
    except ValueError as exc:
        print(str(exc))
        return 1

    selected_ids = ",".join(item["case_id"] for item in selected)
    print("\n\u672c\u6b21\u5c06\u8fd0\u884c\uff1a")
    for item in selected:
        modules = " -> ".join(item["module_chain_labels"]) or "-"
        print(f"- {item['case_id']} | {item['case_name']} | \u6a21\u5757\u94fe: {modules}")

    os.environ[CASE_FILTER_ENV] = selected_ids
    try:
        return pytest.main(["-m", "ui", "--run-ui", "tests/smoke/test_patient_ui_flow.py", "-q"])
    finally:
        os.environ.pop(CASE_FILTER_ENV, None)


if __name__ == "__main__":
    raise SystemExit(main())
