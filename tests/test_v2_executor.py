from __future__ import annotations

from pathlib import Path

from heeg_auto.v2.asset_store import V2AssetStore
from heeg_auto.v2.case_loader import V2CaseLoader
from heeg_auto.v2.executor import V2CaseExecutor


class _FakeActions:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def click(self, **kwargs):
        self.calls.append(("click", kwargs))

    def double_click(self, **kwargs):
        self.calls.append(("double_click", kwargs))

    def right_click(self, **kwargs):
        self.calls.append(("right_click", kwargs))

    def wait_for_window(self, **kwargs):
        self.calls.append(("wait_for_window", kwargs))

    def input_text(self, **kwargs):
        self.calls.append(("input_text", kwargs))

    def select_combo(self, **kwargs):
        self.calls.append(("select_combo", kwargs))

    def select_radio(self, **kwargs):
        self.calls.append(("select_radio", kwargs))

    def set_checkbox(self, **kwargs):
        self.calls.append(("set_checkbox", kwargs))

    def assert_window_closed(self, **kwargs):
        self.calls.append(("assert_window_closed", kwargs))

    def assert_text_visible(self, **kwargs):
        self.calls.append(("assert_text_visible", kwargs))


def test_v2_executor_supports_recommended_case_structure(tmp_path: Path):
    windows_dir = tmp_path / "assets" / "windows"
    elements_dir = tmp_path / "assets" / "elements"
    assertions_dir = tmp_path / "assets" / "assertions"
    windows_dir.mkdir(parents=True)
    elements_dir.mkdir(parents=True)
    assertions_dir.mkdir(parents=True)

    (windows_dir / "windows.yaml").write_text(
        """
窗口资产:
  - 窗口标识: main.patient_list
    中文名称: 患者列表
    所属窗口: 数字脑电采集记录软件
    ControlType: Window
    Name: 数字脑电采集记录软件
    ClassName: Window
    是否唯一: 是
  - 窗口标识: dialog.create_patient
    中文名称: 创建患者
    所属窗口: 创建患者
    ControlType: Window
    Name: 创建患者
    ClassName: Window
    是否唯一: 是
""".strip(),
        encoding="utf-8",
    )
    (elements_dir / "elements.yaml").write_text(
        """
元素资产:
  - 元素标识: main.patient_list.new
    中文名称: 新增
    所属窗口: 患者列表
    AutomationId: NewPatient
    ControlType: Button
    Name: 新增
    ClassName: Button
    是否唯一: 是
  - 元素标识: dialog.create_patient.patient_name
    中文名称: 患者姓名
    所属窗口: 创建患者
    AutomationId: PatientName
    ControlType: Edit
    ClassName: TextBox
    是否唯一: 是
  - 元素标识: dialog.create_patient.gender
    中文名称: 性别
    所属窗口: 创建患者
    AutomationId: PatientGender
    ControlType: ComboBox
    ClassName: ComboBox
    是否唯一: 是
  - 元素标识: dialog.create_patient.left_hand
    中文名称: 左利手
    所属窗口: 创建患者
    AutomationId: PatienLeftHand
    ControlType: RadioButton
    Name: 左利手
    ClassName: RadioButton
    是否唯一: 是
  - 元素标识: dialog.create_patient.ok
    中文名称: 确定
    所属窗口: 创建患者
    AutomationId: OK
    ControlType: Button
    Name: 确定
    ClassName: Button
    是否唯一: 是
""".strip(),
        encoding="utf-8",
    )
    (assertions_dir / "assertions.yaml").write_text(
        """
断言资产:
  - 断言标识: patient.create.opened
    中文名称: 创建患者窗口打开
    检查项:
      - 动作: 等待窗口
        窗口: 创建患者
  - 断言标识: patient.create.success
    中文名称: 创建患者成功
    检查项:
      - 动作: 断言窗口关闭
        窗口: 创建患者
      - 动作: 断言文本可见
        文本: ${患者姓名}
""".strip(),
        encoding="utf-8",
    )

    case_file = tmp_path / "v2_case.yaml"
    case_file.write_text(
        """
用例编号: V2_PATIENT_001
用例名称: 新建患者_正常创建
步骤:
  - 名称: 打开创建患者窗口
    窗口: 患者列表
    按钮: 新增
    断言: 创建患者窗口打开
  - 名称: 填写创建患者表单
    窗口: 创建患者
    参数:
      患者姓名: 哈哈123
      性别: 女
      左利手: 左利手
  - 名称: 提交创建患者
    窗口: 创建患者
    按钮: 确定
    断言: 创建患者成功
""".strip(),
        encoding="utf-8",
    )

    actions = _FakeActions()
    payload = V2CaseLoader().load(case_file)
    result = V2CaseExecutor(asset_store=V2AssetStore(root_dir=tmp_path / "assets")).run_case(actions, payload)

    assert result["summary"]["planned_runs"] == 1
    assert result["summary"]["passed_runs"] == 1
    assert actions.calls[0][0] == "click"
    assert actions.calls[1][0] == "wait_for_window"
    assert actions.calls[2][0] == "input_text"
    assert actions.calls[2][1]["value"] == "哈哈123"
    assert actions.calls[3][0] == "select_combo"
    assert actions.calls[3][1]["value"] == "女"
    assert actions.calls[4][0] == "select_radio"
    assert actions.calls[5][0] == "click"
    assert actions.calls[6][0] == "assert_window_closed"
    assert actions.calls[7][0] == "assert_text_visible"
    assert actions.calls[7][1]["text"] == "哈哈123"


def test_v2_executor_supports_double_click_right_click_and_checkbox(tmp_path: Path):
    windows_dir = tmp_path / "assets" / "windows"
    elements_dir = tmp_path / "assets" / "elements"
    assertions_dir = tmp_path / "assets" / "assertions"
    windows_dir.mkdir(parents=True)
    elements_dir.mkdir(parents=True)
    assertions_dir.mkdir(parents=True)

    (windows_dir / "windows.yaml").write_text(
        """
窗口资产:
  - 窗口标识: main.patient_list
    中文名称: 患者列表
    所属窗口: 数字脑电采集记录软件
    ControlType: Window
    Name: 数字脑电采集记录软件
    ClassName: Window
    是否唯一: 是
  - 窗口标识: dialog.settings
    中文名称: 通用设置
    所属窗口: 通用设置
    ControlType: Window
    Name: 通用设置
    ClassName: Window
    是否唯一: 是
""".strip(),
        encoding="utf-8",
    )
    (elements_dir / "elements.yaml").write_text(
        """
元素资产:
  - 元素标识: main.patient_list.first_row
    中文名称: 患者列表第一行
    所属窗口: 患者列表
    ControlType: DataItem
    ClassName: DataGridRow
    是否唯一: 否
  - 元素标识: dialog.settings.auto_upload
    中文名称: 自动上传
    所属窗口: 通用设置
    AutomationId: AutoUpload
    ControlType: CheckBox
    ClassName: CheckBox
    是否唯一: 是
""".strip(),
        encoding="utf-8",
    )
    (assertions_dir / "assertions.yaml").write_text("断言资产: []", encoding="utf-8")

    case_file = tmp_path / "interaction_case.yaml"
    case_file.write_text(
        """
用例编号: V2_INTERACTION_001
用例名称: 双击右键和复选框
步骤:
  - 名称: 双击患者行
    窗口: 患者列表
    元素: 患者列表第一行
    动作: 双击
  - 名称: 右键患者行
    窗口: 患者列表
    元素: 患者列表第一行
    动作: 右键
  - 名称: 设置复选框
    窗口: 通用设置
    参数:
      自动上传: 是
""".strip(),
        encoding="utf-8",
    )

    actions = _FakeActions()
    payload = V2CaseLoader().load(case_file)
    result = V2CaseExecutor(asset_store=V2AssetStore(root_dir=tmp_path / "assets")).run_case(actions, payload)

    assert result["status"] == "PASS"
    assert actions.calls[0][0] == "double_click"
    assert actions.calls[1][0] == "right_click"
    assert actions.calls[2][0] == "set_checkbox"
    assert actions.calls[2][1]["value"] == "是"