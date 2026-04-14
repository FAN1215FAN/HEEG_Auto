from __future__ import annotations

from pathlib import Path

import pytest

from heeg_auto.pages.create_patient_dialog import CreatePatientDialogPage
from heeg_auto.runner.case_resolver import load_case_payload
from heeg_auto.runner.step_case_loader import StepCaseLoader


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


def test_real_patient_case_now_uses_step_structure():
    payload = load_case_payload("src/heeg_auto/cases/患者检查管理/患者管理/新建患者_正常创建.yaml")

    assert payload["case_format"] == "step"
    assert payload["case_id"] == "患者管理_01"
    assert payload["steps"][0]["button"] == "新增"
    assert payload["steps"][1]["field_params"]["病历号"] == "test123"
    assert payload["steps"][2]["assertions"] == ["创建患者成功"]


def test_real_device_case_now_uses_step_structure():
    payload = load_case_payload("src/heeg_auto/cases/系统设置/设备设置/设备设置循环.yaml")

    assert payload["case_format"] == "step"
    assert payload["case_id"] == "设备设置_02"
    assert payload["loop_count"] == 2
    assert payload["steps"][1]["field_params"]["IP地址1"] == "192.168.1.100"


def test_real_device_variant_case_keeps_multi_param_variant():
    payload = load_case_payload("src/heeg_auto/cases/系统设置/设备设置/设备设置_采样率校验.yaml")

    assert payload["case_format"] == "step"
    assert payload["variant"]["params"] == [
        {"param": "device_type", "param_label": "设备类型"},
        {"param": "sample_rate", "param_label": "采样率"},
        {"param": "gain_value", "param_label": "设备增益"},
    ]
    assert payload["variant"]["values"][1]["mapping"] == {
        "device_type": "Neusen U32",
        "sample_rate": "2000",
        "gain_value": "8",
    }


def test_loader_supports_multi_param_variant_rows_with_parentheses_syntax(tmp_path: Path):
    case_file = tmp_path / "step_case.yaml"
    case_file.write_text(
        """
用例编号: STEP_DEVICE_001
用例名称: 设备设置_多参数变参
变参:
  参数: 设备类型, 采样率, 设备增益
  候选值:
    - (Neusen HEEG,1000,6)
    - (Neusen U32,2000,8)
步骤:
  - 名称: 填写设备设置表单
    窗口: 设备设置
    参数:
      设备类型: ${设备类型}
      采样率: ${采样率}
      设备增益: ${设备增益}
      IP地址: 192.168.1.123
""".strip(),
        encoding="utf-8",
    )

    payload = StepCaseLoader().load(case_file)

    assert payload["variant"]["params"] == [
        {"param": "device_type", "param_label": "设备类型"},
        {"param": "sample_rate", "param_label": "采样率"},
        {"param": "gain_value", "param_label": "设备增益"},
    ]
    assert payload["variant"]["values"][1]["mapping"] == {
        "device_type": "Neusen U32",
        "sample_rate": "2000",
        "gain_value": "8",
    }
    assert payload["steps"][0]["field_params"]["设备类型"] == "${设备类型}"
    assert payload["steps"][0]["field_params"]["采样率"] == "${采样率}"
    assert payload["steps"][0]["field_params"]["设备增益"] == "${设备增益}"


def test_loader_rejects_duplicate_yaml_keys(tmp_path: Path):
    case_file = tmp_path / "duplicate.yaml"
    case_file.write_text(
        """
用例编号: TC_DUP_001
用例名称: 重复键
标签:
  - smoke
步骤:
  - 名称: 填写
    窗口: 设备设置
    参数:
      采样率: 1000
      采样率: 2000
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="重复键"):
        StepCaseLoader().load(case_file)


def test_loader_preserves_actual_double_quote_content_with_single_quote_wrapper(tmp_path: Path):
    case_file = tmp_path / "quoted.yaml"
    case_file.write_text(
        """
用例编号: TC_QUOTE_001
用例名称: 双引号输入
步骤:
  - 名称: 填写患者表单
    窗口: 新建患者
    参数:
      患者姓名: 张三
      病历号: '"123"'
""".strip(),
        encoding="utf-8",
    )

    payload = StepCaseLoader().load(case_file)

    assert payload["steps"][0]["field_params"]["病历号"] == '"123"'


def test_loader_supports_loop_count_and_stop_on_failure_flags(tmp_path: Path):
    case_file = tmp_path / "loop.yaml"
    case_file.write_text(
        """
用例编号: TC_LOOP_001
用例名称: 循环
循环次数: 3
失败即停: 是
步骤:
  - 名称: 启动软件
    动作: 启动应用
    参数:
      会话模式: 自动
""".strip(),
        encoding="utf-8",
    )

    payload = StepCaseLoader().load(case_file)

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
