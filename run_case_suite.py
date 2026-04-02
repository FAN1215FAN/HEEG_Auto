from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from heeg_auto.core.reporting import generate_suite_reports
from heeg_auto.runner.formal_case_runner import FormalCaseRunner
from tests.support.case_catalog import build_directory_catalog, load_case_catalog


def _format_case_line(item: dict) -> str:
    modules = " -> ".join(item["module_chain_labels"]) or "-"
    suffix = f" | {item['plan_label']}" if item.get("plan_label") else ""
    return f"{item['case_id']} | {item['case_name']} | 目录: {item['relative_dir']} | 模块链: {modules}{suffix}"


def _print_case_catalog(catalog: list[dict]) -> None:
    print("\n可运行的正式 case 列表：")
    for index, item in enumerate(catalog, start=1):
        print(f"  {index}. {_format_case_line(item)}")


def _print_directory_catalog(directory_catalog: list[dict]) -> None:
    print("\n可批量运行的文件夹：")
    for item in directory_catalog:
        joined = "、".join(item["case_ids"])
        folder_name = Path(item["directory"]).name if item["directory"] != "根目录" else "根目录"
        print(f"  - {folder_name} ({item['count']}条): {joined}")


def _normalize_directory_text(text: str) -> str:
    normalized = text.strip().replace("\\", "/").replace("／", "/")
    return "/".join(part.strip() for part in normalized.split("/") if part.strip())


def _match_directory_key(directory_token: str, by_directory: dict[str, list[dict]]) -> str:
    normalized_token = _normalize_directory_text(directory_token)
    if not normalized_token:
        raise ValueError("文件夹名称不能为空。")
    if "/" in normalized_token:
        raise ValueError(f"请输入文件夹名称，不要输入完整目录：{directory_token}")

    segment_map: dict[str, list[str]] = {}
    for directory in by_directory:
        normalized_directory = _normalize_directory_text(directory)
        for segment in [part for part in normalized_directory.split("/") if part]:
            segment_map.setdefault(segment, []).append(directory)

    matches = segment_map.get(normalized_token, [])
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        joined = "、".join(sorted(matches))
        raise ValueError(f"文件夹名称匹配到多个目录：{joined}。请改成更具体且唯一的文件夹名称。")
    raise ValueError(f"无效文件夹：{directory_token}。请输入列表里展示的文件夹名称，例如：患者管理。")


def _resolve_selection(catalog: list[dict], raw: str) -> list[dict]:
    raw = raw.strip()
    if not raw or raw.lower() in {"all", "a", "全部"}:
        return catalog
    by_index = {str(index): item for index, item in enumerate(catalog, start=1)}
    by_case_id = {item["case_id"]: item for item in catalog}
    by_directory: dict[str, list[dict]] = {}
    for item in catalog:
        by_directory.setdefault(item["relative_dir"], []).append(item)

    selected: list[dict] = []
    seen: set[str] = set()
    tokens = [part.strip() for part in raw.split(",") if part.strip()]
    for token in tokens:
        item = by_index.get(token) or by_case_id.get(token)
        if item is not None:
            if item["case_id"] not in seen:
                selected.append(item)
                seen.add(item["case_id"])
            continue

        directory_key = _match_directory_key(token, by_directory)
        for directory_item in by_directory[directory_key]:
            if directory_item["case_id"] not in seen:
                selected.append(directory_item)
                seen.add(directory_item["case_id"])

    if not selected:
        raise ValueError("至少选择一条 case。")
    return selected


def _prompt_selection(catalog: list[dict]) -> list[dict]:
    while True:
        raw = input("请选择要运行的 case、编号，或文件夹名称：").strip()
        try:
            return _resolve_selection(catalog, raw)
        except ValueError as exc:
            print(str(exc))
            print("请重新输入，例如：1、患者管理_01、患者管理。")


def _print_execution_result(result: dict) -> None:
    summary = result.get("summary", {})
    print(f"  结果: {result.get('status', '-')}")
    print(
        "  计划: "
        f"planned={summary.get('planned_runs', 0)}, "
        f"executed={summary.get('executed_runs', 0)}, "
        f"passed={summary.get('passed_runs', 0)}, "
        f"failed={summary.get('failed_runs', 0)}, "
        f"interrupted={summary.get('interrupted_runs', 0)}, "
        f"not_run={summary.get('not_run_runs', 0)}"
    )
    if result.get("error_summary"):
        print(f"  原因: {result['error_summary']}")


def _build_loader_failure_result(item: dict, exc: Exception) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "case_id": item["case_id"],
        "case_name": item["case_name"],
        "case_path": str(item["path"]),
        "relative_dir": item["relative_dir"],
        "tags": item.get("tags", []),
        "module_chain_labels": item.get("module_chain_labels", []),
        "variant": item.get("variant"),
        "loop_count": item.get("loop_count", 1),
        "stop_on_failure": True,
        "passed": False,
        "status": "INTERRUPTED",
        "context": {},
        "started_at": now,
        "finished_at": now,
        "duration_seconds": 0,
        "report_timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "execution_results": [
            {
                "sequence": 1,
                "execution_id": f"{item['case_id']}#01",
                "execution_name": item["case_name"],
                "loop_index": 1,
                "loop_total": 1,
                "variant": None,
                "status": "INTERRUPTED",
                "passed": False,
                "started_at": now,
                "finished_at": now,
                "duration_seconds": 0,
                "module_results": [],
                "error_summary": str(exc) or exc.__class__.__name__,
                "error_detail": traceback.format_exc(),
                "failure": {},
                "artifact_paths": [],
                "parameter_snapshot": [],
            }
        ],
        "summary": {
            "planned_runs": 1,
            "executed_runs": 1,
            "passed_runs": 0,
            "failed_runs": 0,
            "interrupted_runs": 1,
            "not_run_runs": 0,
        },
        "module_results": [],
        "error_summary": str(exc) or exc.__class__.__name__,
        "error_detail": traceback.format_exc(),
        "failure": {},
        "artifact_paths": [],
        "environment": {},
    }


def main() -> int:
    catalog = load_case_catalog()
    if not catalog:
        print("未发现任何正式 case。")
        return 1

    _print_case_catalog(catalog)
    _print_directory_catalog(build_directory_catalog())
    print("\n输入 all / 全部 可运行所有 case；也可输入序号、case 编号，或直接输入文件夹名称批量运行，多个用逗号分隔。")
    selected = _prompt_selection(catalog)

    print("\n本次将运行：")
    for item in selected:
        print(f"- {_format_case_line(item)}")

    runner = FormalCaseRunner()
    suite_results: list[dict] = []
    for index, item in enumerate(selected, start=1):
        print(f"\n[{index}/{len(selected)}] 开始执行：{item['case_id']} | {item['case_name']}")
        try:
            result = runner.run_case(item["path"], raise_on_failure=False, close_after_run=False)
        except Exception as exc:
            result = _build_loader_failure_result(item, exc)
        result["relative_dir"] = item["relative_dir"]
        suite_results.append(result)
        _print_execution_result(result)

    report_files = generate_suite_reports(suite_results)
    passed_cases = sum(1 for item in suite_results if item.get("status") == "PASS")
    failed_cases = sum(1 for item in suite_results if item.get("status") == "FAIL")
    interrupted_cases = sum(1 for item in suite_results if item.get("status") == "INTERRUPTED")

    print("\n执行完成：")
    print(f"  成功: {passed_cases}")
    print(f"  失败: {failed_cases}")
    print(f"  异常中断: {interrupted_cases}")
    print(f"  HTML 报告: {report_files['html_path']}")

    if failed_cases or interrupted_cases:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
