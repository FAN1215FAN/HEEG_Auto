from __future__ import annotations

from tests.support.case_catalog import build_directory_catalog, load_case_catalog


def test_case_catalog_keeps_requested_order():
    catalog = load_case_catalog(["设备设置_01", "患者管理_01", "启动软件_01"])

    assert [item["case_id"] for item in catalog] == ["设备设置_01", "患者管理_01", "启动软件_01"]


def test_case_catalog_exposes_step_plan_label_and_directory():
    item = next(case for case in load_case_catalog() if case["case_id"] == "设备设置_01")

    assert "变参: 设备类型、采样率、设备增益 / 3组" in item["plan_label"]
    assert "步骤: 3步" in item["plan_label"]
    assert item["relative_dir"] == "系统设置/设备设置"
    assert item["file_name"] == "设备设置_采样率校验.yaml"


def test_directory_catalog_collects_cases_by_physical_directory():
    directory = next(item for item in build_directory_catalog() if item["directory"] == "患者检查管理/患者管理")

    assert directory["count"] == 2
    assert directory["case_ids"] == ["患者管理_01", "患者管理_02"]


def test_case_catalog_supports_directory_filter():
    catalog = load_case_catalog(selected_case_dirs=["设备设置"])

    assert [item["case_id"] for item in catalog] == ["设备设置_01", "设备设置_02"]


def test_case_catalog_supports_single_file_filter():
    catalog = load_case_catalog(selected_case_file="src/heeg_auto/cases/系统设置/设备设置/设备设置_采样率校验.yaml")

    assert [item["case_id"] for item in catalog] == ["设备设置_01"]
