from __future__ import annotations

from heeg_auto.config.settings import DEFAULT_CASE_PATH
from heeg_auto.runner.case_loader import FormalCaseLoader


def test_default_case_uses_chinese_formal_case_schema():
    payload = FormalCaseLoader().load(DEFAULT_CASE_PATH)

    assert payload["case_id"] == "TC_PATIENT_001"
    assert payload["case_name"] == "\u65b0\u5efa\u60a3\u8005_\u6b63\u5e38\u521b\u5efa"
    assert payload["module_chain"][0]["module"] == "patient.create"
    assert payload["session_policy"] == "\u81ea\u52a8"
    assert payload["module_chain"][0]["params"]["name"].startswith("autopatient")


def test_second_case_reuses_existing_session_policy():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/patient/TC_PATIENT_002.yaml")

    assert payload["case_id"] == "TC_PATIENT_002"
    assert payload["session_policy"] == "\u590d\u7528\u5df2\u6709\u5e94\u7528"
