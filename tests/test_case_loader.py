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


def test_patient_positive_case_matches_assertion_group_style():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/患者检查管理/患者管理/1新建患者_正常创建.yaml")
    assert payload["case_id"] == "患者管理_01"
    assert payload["case_name"] == "新建患者_正常创建"
    assert payload["data"] == {}
    assert [entry["module"] for entry in payload["module_chain"]] == ["system.launch", "patient.create"]
    assert payload["module_chain"][1]["params"]["patient_name"] == "哈哈123"
    assert payload["module_chain"][1]["params"]["eeg_id"] == "123456"
    assert payload["module_chain"][1]["assertion_group"] == "创建成功"


def test_patient_negative_case_uses_failure_assertion_group():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/患者检查管理/患者管理/新建患者_姓名含特殊字符.yaml")
    assert payload["case_id"] == "患者管理_02"
    assert payload["module_chain"][0]["params"]["gender"] == "男"
    assert payload["module_chain"][0]["params"]["expect_error_contains"] == "患者姓名不能包含特殊字符"
    assert payload["module_chain"][0]["assertion_group"] == "创建失败"


def test_device_case_uses_configured_launch_module_and_text_normalization():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/系统设置/设备设置/设备设置循环.yaml")
    assert payload["case_id"] == "设备设置_02"
    assert [entry["module"] for entry in payload["module_chain"]] == ["device.settings"]
    assert payload["module_chain"][0]["params"]["sample_rate"] == "2000"
    assert payload["module_chain"][0]["params"]["gain_value"] == "6"
    assert payload["module_chain"][0]["assertion_group"] == "设置成功"


def test_long_case_supports_variant_definition_without_quotes():
    payload = FormalCaseLoader().load("src/heeg_auto/cases/系统设置/设备设置/采样率校验.yaml")
    assert payload["case_id"] == "设备设置_01"
    assert payload["variant"] == {
        "module": "device.settings",
        "module_label": "设备设置",
        "param": "sample_rate",
        "param_label": "采样率",
        "values": ["1000", "2000", "4000"],
    }
    assert payload["module_chain"][1]["params"]["sample_rate"] == "${变参值}"
    assert payload["module_chain"][1]["params"]["ip_address"] == "192.168.1.123"
    assert payload["loop_count"] == 1
    assert payload["stop_on_failure"] is True


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
      采样率: 1000
      采样率: 2000
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="重复键"):
        FormalCaseLoader().load(case_file)


def test_loader_preserves_actual_double_quote_content_with_single_quote_wrapper(tmp_path):
    case_file = tmp_path / "quoted.yaml"
    case_file.write_text(
        """
用例编号: TC_QUOTE_001
用例名称: 双引号输入
模块链:
  - 模块: 新建患者
    参数:
      患者姓名: 张三
      病历号: '"123"'
    断言组: 创建成功
""".strip(),
        encoding="utf-8",
    )

    payload = FormalCaseLoader().load(case_file)

    assert payload["module_chain"][0]["params"]["patient_id"] == '"123"'


def test_loader_supports_loop_count_and_stop_on_failure_flags(tmp_path):
    case_file = tmp_path / "loop.yaml"
    case_file.write_text(
        """
用例编号: TC_LOOP_001
用例名称: 循环
循环次数: 3
失败即停: 是
模块链:
  - 模块: 启动软件
    参数:
      会话模式: 自动
""".strip(),
        encoding="utf-8",
    )

    payload = FormalCaseLoader().load(case_file)

    assert payload["loop_count"] == 3
    assert payload["stop_on_failure"] is True


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
