from __future__ import annotations

from pathlib import Path

from heeg_auto.assets.asset_store import AssetStore
from heeg_auto.runner.step_case_executor import StepCaseExecutor
from heeg_auto.runner.step_case_loader import StepCaseLoader


class _FakeActions:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def click(self, **kwargs):
        self.calls.append(("click", kwargs))

    def wait_for_window(self, **kwargs):
        self.calls.append(("wait_for_window", kwargs))

    def assert_text_visible(self, **kwargs):
        self.calls.append(("assert_text_visible", kwargs))


def test_step_case_executor_uses_formal_runner_entry_names(tmp_path: Path):
    windows_dir = tmp_path / "assets" / "windows"
    elements_dir = tmp_path / "assets" / "elements"
    assertions_dir = tmp_path / "assets" / "assertions"
    windows_dir.mkdir(parents=True)
    elements_dir.mkdir(parents=True)
    assertions_dir.mkdir(parents=True)

    (windows_dir / "窗口.yaml").write_text(
        """
窗口资产:
  - 窗口标识: window.main
    中文名称: 主窗口
    所属窗口: 主窗口
    ControlType: Window
    Name: 主窗口
""".strip(),
        encoding="utf-8",
    )
    (elements_dir / "元素.yaml").write_text(
        """
元素资产:
  - 元素标识: element.open
    中文名称: 打开
    所属窗口: 主窗口
    AutomationId: Open
    ControlType: Button
    Name: 打开
""".strip(),
        encoding="utf-8",
    )
    (assertions_dir / "断言.yaml").write_text(
        """
断言资产:
  - 断言标识: assertion.ready
    中文名称: 已准备
    检查项:
      - 动作: 等待窗口
        窗口: 主窗口
      - 动作: 断言文本可见
        窗口: 主窗口
        文本: 就绪
""".strip(),
        encoding="utf-8",
    )

    case_file = tmp_path / "step_case.yaml"
    case_file.write_text(
        """
用例编号: STEP_001
用例名称: 正式步骤式入口
步骤:
  - 名称: 打开页面
    窗口: 主窗口
    按钮: 打开
    断言: 已准备
""".strip(),
        encoding="utf-8",
    )

    payload = StepCaseLoader().load(case_file)
    result = StepCaseExecutor(asset_store=AssetStore(root_dir=tmp_path / "assets")).run_case(_FakeActions(), payload)

    assert result["status"] == "PASS"
