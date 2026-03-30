from __future__ import annotations

from heeg_auto.core.base_page import BasePage


def test_base_page_criteria_ignores_descriptive_locator_fields():
    locator = {
        "label": "新增按钮",
        "page": "main",
        "automation_id": "NewPatient",
        "control_type": "Button",
    }

    criteria = BasePage._criteria(locator)

    assert criteria == {
        "auto_id": "NewPatient",
        "control_type": "Button",
    }