from __future__ import annotations

from pathlib import Path

from heeg_auto.v2.asset_store import V2AssetStore


def test_v2_asset_store_loads_clean_chinese_assets(tmp_path: Path):
    windows_dir = tmp_path / "windows"
    elements_dir = tmp_path / "elements"
    assertions_dir = tmp_path / "assertions"
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
""".strip(),
        encoding="utf-8",
    )

    store = V2AssetStore(root_dir=tmp_path)

    assert store.load_windows()["main.patient_list"]["title"] == "数字脑电采集记录软件"
    assert store.resolve_element("新增", window="患者列表")["automation_id"] == "NewPatient"
    assert store.resolve_assertion("创建患者窗口打开")["checks"][0]["action"] == "等待窗口"