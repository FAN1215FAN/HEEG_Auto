from __future__ import annotations

from heeg_auto.config.locators import resolve_locator
from heeg_auto.core.actions import ActionExecutor


class DummyLogger:
    def info(self, *args, **kwargs):
        return None


class DummyDriver:
    main_window = None


def test_resolve_locator_supports_chinese_alias():
    locator = resolve_locator("新增", default_page="main")
    assert locator["automation_id"] == "NewPatient"
    assert locator["control_type"] == "Button"
    assert locator["page"] == "main"


def test_resolve_locator_supports_direct_text_target():
    locator = resolve_locator("确定", default_page="dialog")
    assert locator["title"] == "确定"
    assert locator["control_type"] == "Button"


def test_resolve_locator_supports_chinese_dict_keys():
    locator = resolve_locator({"自动化ID": "PatientID", "控件类型": "Edit", "页面": "dialog"})
    assert locator == {
        "automation_id": "PatientID",
        "control_type": "Edit",
        "page": "dialog",
    }


def test_action_executor_supports_chinese_action_aliases():
    executor = ActionExecutor(driver=DummyDriver(), logger=DummyLogger())
    assert executor.resolve_action_name("单击") == "click"
    assert executor.resolve_action_name("输入") == "input_text"
