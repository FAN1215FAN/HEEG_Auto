from __future__ import annotations

from datetime import datetime

import pytest

from heeg_auto.config.settings import ensure_artifact_dirs
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger


def _build_case_report_summary(result: dict) -> str:
    summary = result.get("summary", {})
    lines = [
        f"用例: {result.get('case_id', '-')} | {result.get('case_name', '-')}",
        f"状态: {result.get('status', '-')}",
        f"执行计划: planned={summary.get('planned_runs', 0)}, executed={summary.get('executed_runs', 0)}, passed={summary.get('passed_runs', 0)}, failed={summary.get('failed_runs', 0)}, interrupted={summary.get('interrupted_runs', 0)}, not_run={summary.get('not_run_runs', 0)}",
    ]
    first_abnormal = next(
        (item for item in result.get("execution_results", []) if item.get("status") in {"FAIL", "INTERRUPTED"}),
        None,
    )
    if first_abnormal:
        lines.append(f"首个异常轮次: {first_abnormal.get('execution_name', '-')}")
        lines.append(f"异常摘要: {first_abnormal.get('error_summary', '-')}")
    return "\n".join(lines)


def pytest_configure(config):
    ensure_artifact_dirs()


def pytest_addoption(parser):
    parser.addoption(
        "--run-ui",
        action="store_true",
        default=False,
        help="运行真实桌面 UI 自动化用例",
    )
    parser.addoption(
        "--stall-timeout",
        action="store",
        default="60",
        help="真实 UI 执行无进展超时秒数，默认 60 秒",
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when != "call":
        return
    case_result = getattr(item, "case_result", None)
    if not case_result:
        return
    report.sections.append(("case-summary", _build_case_report_summary(case_result)))
    report.case_status = case_result.get("status", "-")
    report.case_directory = getattr(item, "case_directory", "-")
    report.failure_summary = case_result.get("error_summary", "")


@pytest.fixture
def app_driver(request):
    logger = build_logger(name="pytest_run")
    driver = UIADriver(logger=logger)
    request.node.app_driver = driver
    yield driver
    driver.close()


@pytest.fixture(autouse=True)
def failure_screenshot(request):
    yield
    rep_call = getattr(request.node, "rep_call", None)
    driver = getattr(request.node, "app_driver", None)
    if rep_call and rep_call.failed and driver:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        saved_paths = driver.capture_failure_artifacts(
            case_name=request.node.name,
            step_name=f"pytest_{rep_call.when}",
            timestamp=timestamp,
        )
        for path in saved_paths:
            logger = getattr(driver, "logger", None)
            if logger:
                logger.error("failure.artifact %s", path)
