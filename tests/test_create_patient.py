from __future__ import annotations

from heeg_auto.config.settings import DEFAULT_CASE_PATH
from heeg_auto.core.case_runner import CaseRunner


def test_create_patient_smoke():
    runner = CaseRunner()
    result = runner.run_case(DEFAULT_CASE_PATH)
    assert result["passed"] is True
    assert result["context"]["patient_name"].startswith("auto_patient_")
