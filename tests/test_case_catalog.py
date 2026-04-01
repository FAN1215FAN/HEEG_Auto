from __future__ import annotations

from tests.support.case_catalog import load_case_catalog


def test_case_catalog_keeps_requested_order():
    catalog = load_case_catalog(["TC_PATIENT_002", "TC_PATIENT_001", "TC_DEVICE_001"])
    assert [item["case_id"] for item in catalog] == ["TC_PATIENT_002", "TC_PATIENT_001", "TC_DEVICE_001"]