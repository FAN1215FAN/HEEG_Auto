from __future__ import annotations

import pytest

from heeg_auto.pages.create_patient_dialog import CreatePatientDialogPage
from heeg_auto.runner.case_loader import FormalCaseLoader


class _DialogWrapper:
    def __init__(self, title: str, handle: int, descendants=None) -> None:
        self._title = title
        self.handle = handle
        self._descendants = descendants or []
        self.element_info = type("Info", (), {"name": title, "control_type": "Window"})()

    def window_text(self):
        return self._title

    def descendants(self):
        return self._descendants

    def is_visible(self):
        return True


class _Desktop:
    def __init__(self, wrapper):
        self._wrapper = wrapper

    def top_window(self):
        return self._wrapper

    def window(self, handle):
        return type("WindowSpec", (), {"exists": lambda self, timeout=0.2: True})()


class _Driver:
    def __init__(self) -> None:
        dialog_marker = _DialogWrapper("设备设置", 3)
        self.main_window = _DialogWrapper("主窗口", 1)
        self.main_window_wrapper = self.main_window
        self._dialog = _DialogWrapper("", 2, descendants=[dialog_marker])
        self.desktop = _Desktop(self._dialog)

    def top_window(self):
        return self._dialog


class _MainOnlyDriver:
    def __init__(self) -> None:
        self.main_window = _DialogWrapper("主窗口", 1)
        self.main_window_wrapper = self.main_window
        self.desktop = _Desktop(self.main_window)

    def top_window(self):
        return self.main_window


class _Logger:
    def info(self, *args, **kwargs):
        return None


def test_patient_positive_case_matches_current_direct_parameter_style():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/patient/TC_PATIENT_001.yaml")
    assert payload["case_id"] == "TC_PATIENT_001"
    assert payload["case_name"] == "正常创建"
    assert payload["data"] == {}
    assert payload["module_chain"][0]["module"] == "patient.create"
    assert payload["module_chain"][0]["params"]["patient_name"] == "哈哈123"
    assert payload["module_chain"][0]["params"]["habit_hand"] == "右手"


def test_patient_negative_case_matches_current_direct_parameter_style():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/patient/TC_PATIENT_002.yaml")
    assert payload["case_id"] == "TC_PATIENT_002"
    assert payload["data"] == {}
    assert payload["module_chain"][0]["params"]["gender"] == "女"
    assert payload["module_chain"][0]["params"]["expect_status"] == "FAIL"
    assert payload["module_chain"][0]["params"]["expect_error_contains"] == "患者姓名不能包含特殊字符"


def test_device_case_matches_current_single_module_style():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/device/TC_DEVICE_001.yaml")
    assert payload["case_id"] == "TC_DEVICE_001"
    assert payload["data"] == {}
    assert [entry["module"] for entry in payload["module_chain"]] == ["device.settings"]
    assert payload["module_chain"][0]["params"]["device_type"] == "Neusen HEEG"


def test_long_case_supports_multiple_modules_without_data_layer():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/long/TC_LONG_001.yaml")
    assert payload["case_id"] == "TC_LONG_001"
    assert payload["data"] == {}
    assert [entry["module"] for entry in payload["module_chain"]] == [
        "system.launch",
        "device.settings",
        "patient.create",
    ]
    assert payload["module_chain"][1]["params"]["sample_rate"] == ["1000", "2000", "4000"]
    assert payload["module_chain"][1]["params"]["ip_address"] == "192.168.1.100"
    assert payload["module_chain"][2]["params"]["habit_hand"] == "左手"


def test_loader_rejects_duplicate_yaml_keys(tmp_path):
    case_file = tmp_path / "duplicate.yaml"
    case_file.write_text(
        """
用例编号: TC_DUP_001
用例名称: 重复键
标签:
  - smoke
模块链:
  - 模块: 设备设置
    参数:
      采样率: "1000"
      采样率: "2000"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="重复键"):
        FormalCaseLoader().load(case_file)


def test_dialog_page_prefers_active_dialog_window_after_open():
    page = CreatePatientDialogPage(driver=_Driver(), logger=_Logger())

    root = page.wait_open(marker_text="设备设置", timeout=1)

    assert root.handle == 2
    assert page.root.handle == 2


def test_dialog_page_wait_open_rejects_main_window_text_false_positive():
    page = CreatePatientDialogPage(driver=_MainOnlyDriver(), logger=_Logger())

    with pytest.raises(TimeoutError, match="未出现"):
        page.wait_open(marker_text="设备设置", timeout=1)


def test_dialog_page_wait_closed_accepts_marker_disappearance_even_if_cached_handle_still_exists():
    page = CreatePatientDialogPage(driver=_Driver(), logger=_Logger())
    page.wait_open(marker_text="设备设置", timeout=1)
    page._iter_visible_texts_from_roots = lambda: iter(["数字脑电采集记录软件"])

    page.wait_closed(timeout=1)

    assert page.root is None
