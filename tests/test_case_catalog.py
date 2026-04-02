from __future__ import annotations

from tests.support.case_catalog import build_directory_catalog, load_case_catalog


def test_case_catalog_keeps_requested_order():
    catalog = load_case_catalog(["患者管理_02", "患者管理_01", "设备设置_01"])
    assert [item["case_id"] for item in catalog] == ["患者管理_02", "患者管理_01", "设备设置_01"]


def test_case_catalog_exposes_variant_plan_label_and_chinese_directory():
    item = next(case for case in load_case_catalog() if case["case_id"] == "设备设置_01")

    assert item["plan_label"] == "变参: 设备设置 / 采样率 / 3值"
    assert item["relative_dir"] == "系统设置/设备设置"
    assert item["file_name"] == "采样率校验.yaml"


def test_directory_catalog_collects_cases_by_physical_directory():
    directory = next(item for item in build_directory_catalog() if item["directory"] == "患者检查管理/患者管理")

    assert directory["count"] == 2
    assert directory["case_ids"] == ["患者管理_01", "患者管理_02"]
