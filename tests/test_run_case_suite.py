from __future__ import annotations

import pytest

import run_case_suite


@pytest.fixture
def sample_catalog() -> list[dict]:
    return [
        {
            "case_id": "患者管理_01",
            "case_name": "新建患者_正常创建",
            "relative_dir": "患者检查管理/患者管理",
            "module_chain_labels": ["新建患者"],
            "plan_label": "",
        },
        {
            "case_id": "患者管理_02",
            "case_name": "新建患者_姓名含特殊字符",
            "relative_dir": "患者检查管理/患者管理",
            "module_chain_labels": ["新建患者"],
            "plan_label": "",
        },
        {
            "case_id": "设备设置_01",
            "case_name": "采样率校验",
            "relative_dir": "系统设置/设备设置",
            "module_chain_labels": ["设备设置"],
            "plan_label": "",
        },
    ]


def test_resolve_selection_supports_leaf_directory_name(sample_catalog):
    selected = run_case_suite._resolve_selection(sample_catalog, "患者管理")

    assert [item["case_id"] for item in selected] == ["患者管理_01", "患者管理_02"]


def test_resolve_selection_rejects_full_directory_path(sample_catalog):
    with pytest.raises(ValueError, match="请输入文件夹名称"):
        run_case_suite._resolve_selection(sample_catalog, "患者检查管理/患者管理")


def test_resolve_selection_reports_ambiguous_directory():
    catalog = [
        {
            "case_id": "A",
            "case_name": "示例A",
            "relative_dir": "患者检查管理/患者管理",
            "module_chain_labels": [],
            "plan_label": "",
        },
        {
            "case_id": "B",
            "case_name": "示例B",
            "relative_dir": "归档/患者管理",
            "module_chain_labels": [],
            "plan_label": "",
        },
    ]

    with pytest.raises(ValueError, match="文件夹名称匹配到多个目录"):
        run_case_suite._resolve_selection(catalog, "患者管理")
