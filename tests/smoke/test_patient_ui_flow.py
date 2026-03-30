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


@pytest.mark.parametrize("case_file", build_case_params(ui=True))
def test_formal_cases_ui_smoke(case_file: Path, pytestconfig, ui_suite_runner: FormalCaseRunner):
    if not pytestconfig.getoption("--run-ui"):
        pytest.skip("未显式开启真实桌面联调，请追加 --run-ui")

    result = ui_suite_runner.run_case(case_file, raise_on_failure=False, close_after_run=False)
    assert result["passed"] is True