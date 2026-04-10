from __future__ import annotations

from pathlib import Path

import pytest

from heeg_auto.runner.formal_case_runner import FormalCaseRunner
from heeg_auto.runner.formal_suite_service import FormalSuiteService
from tests.support.case_catalog import build_case_item_params


def _should_execute_formal_ui(pytestconfig) -> bool:
    return any(
        [
            bool(pytestconfig.getoption("--run-ui")),
            bool(pytestconfig.getoption("--run-formal")),
            bool((pytestconfig.getoption("--case-id") or "").strip()),
            bool((pytestconfig.getoption("--case-dir") or "").strip()),
            bool((pytestconfig.getoption("--case-file") or "").strip()),
        ]
    )


@pytest.fixture(scope="module")
def ui_suite_service(pytestconfig):
    service = FormalSuiteService(stall_timeout_seconds=int(pytestconfig.getoption("--stall-timeout")))
    yield service
    service.finish()


def test_case_without_launch_module_attaches_existing_session(monkeypatch):
    runner = FormalCaseRunner()
    calls: list[tuple[str | None, str]] = []

    def fake_ensure_session(exe_path: str | None = None, session_mode: str = "自动") -> str:
        calls.append((exe_path, session_mode))
        return "attach"

    monkeypatch.setattr(runner.actions, "ensure_session", fake_ensure_session)
    runner._ensure_execution_session([{"module": "patient.create", "params": {}}], watchdog=type("W", (), {"touch": lambda self, label: None})())

    assert calls == [(None, "复用已有应用")]


def test_case_with_launch_module_does_not_force_extra_attach(monkeypatch):
    runner = FormalCaseRunner()
    calls: list[tuple[str | None, str]] = []

    def fake_ensure_session(exe_path: str | None = None, session_mode: str = "自动") -> str:
        calls.append((exe_path, session_mode))
        return "attach"

    monkeypatch.setattr(runner.actions, "ensure_session", fake_ensure_session)
    runner._ensure_execution_session([{"module": "system.launch", "params": {}}], watchdog=type("W", (), {"touch": lambda self, label: None})())

    assert calls == []


@pytest.mark.formal
@pytest.mark.parametrize("case_item", build_case_item_params(ui=True))
def test_formal_cases_ui_smoke(
    case_item: dict,
    pytestconfig,
    request,
    ui_suite_service: FormalSuiteService,
):
    if not _should_execute_formal_ui(pytestconfig):
        pytest.skip("未选择正式 case 执行范围，请使用 --case-dir、--case-file、--case-id 或 --run-formal")

    result = ui_suite_service.run_case_item(case_item)
    request.node.case_directory = Path(case_item["path"]).parent.name
    request.node.case_result = result
    assert result["passed"] is True
