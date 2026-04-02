from __future__ import annotations

from pathlib import Path

import pytest

from heeg_auto.runner.formal_case_runner import FormalCaseRunner
from tests.support.case_catalog import build_case_params


@pytest.fixture(scope="module")
def ui_suite_runner():
    runner = FormalCaseRunner()
    yield runner
    runner.driver.close()


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


@pytest.mark.parametrize("case_file", build_case_params(ui=True))
def test_formal_cases_ui_smoke(
    case_file: Path,
    pytestconfig,
    request,
    ui_suite_runner: FormalCaseRunner,
):
    if not pytestconfig.getoption("--run-ui"):
        pytest.skip("未显式开启真实界面联调，请追加 --run-ui")

    request.node.case_directory = case_file.parent.name
    result = ui_suite_runner.run_case(
        case_file,
        raise_on_failure=False,
        close_after_run=False,
        stall_timeout_seconds=int(pytestconfig.getoption("--stall-timeout")),
    )
    request.node.case_result = result
    assert result["passed"] is True
