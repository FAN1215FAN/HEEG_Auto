from __future__ import annotations

from pathlib import Path

from heeg_auto.assets.asset_store import AssetStore
from heeg_auto.assets import asset_store as asset_store_module


def test_asset_store_loads_clean_chinese_assets(tmp_path: Path):
    windows_dir = tmp_path / "windows"
    elements_dir = tmp_path / "elements"
    assertions_dir = tmp_path / "assertions"
    windows_dir.mkdir(parents=True)
    elements_dir.mkdir(parents=True)
    assertions_dir.mkdir(parents=True)

    (windows_dir / "窗口.yaml").write_text(
        """
窗口资产:
  - 窗口标识: main.patient_list
    中文名称: 患者列表
    所属窗口: 数字脑电采集记录软件窗口
    ControlType: Window
    Name: 数字脑电采集记录软件
    ClassName: Window
    是否唯一: 是
""".strip(),
        encoding="utf-8",
    )
    (elements_dir / "元素.yaml").write_text(
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
    (assertions_dir / "断言.yaml").write_text(
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

    store = AssetStore(root_dir=tmp_path)

    assert store.load_windows()["main.patient_list"]["title"] == "数字脑电采集记录软件"
    assert store.resolve_element("新增", window="患者列表")["automation_id"] == "NewPatient"
    assert store.resolve_assertion("创建患者窗口打开")["checks"][0]["action"] == "等待窗口"


def test_asset_store_keeps_window_interaction_calibration(tmp_path: Path):
    windows_dir = tmp_path / "windows"
    windows_dir.mkdir(parents=True)
    (windows_dir / "历史回放窗口.yaml").write_text(
        """
窗口资产:
  - 窗口标识: window.history.replay
    中文名称: 历史回放窗口
    所属窗口: 历史回放窗口
    ControlType: Window
    Name: 历史回放
    交互标定:
      波形左比例: 0.13
      波形右比例: 0.92
      波形上比例: 0.10
      波形下比例: 0.88
      进度条左比例: 0.08
      进度条右比例: 0.91
      进度条上比例: 0.92
      进度条下比例: 0.97
""".strip(),
        encoding="utf-8",
    )

    store = AssetStore(root_dir=tmp_path)
    window = store.resolve_window("历史回放窗口")

    assert window["interaction_calibration"]["waveform_left_ratio"] == 0.13
    assert window["interaction_calibration"]["timeline_bottom_ratio"] == 0.97


def test_asset_store_keeps_window_title_empty_when_automation_id_is_present(tmp_path: Path):
    windows_dir = tmp_path / "windows"
    windows_dir.mkdir(parents=True)
    (windows_dir / "剪辑完成窗口.yaml").write_text(
        """
窗口资产:
  - 窗口标识: window.history.clip_complete
    中文名称: 剪辑完成窗口
    所属窗口: 剪辑完成窗口
    AutomationId: MessageBoxTip
    ControlType: Window
    Name:
    ClassName: Window
""".strip(),
        encoding="utf-8",
    )

    store = AssetStore(root_dir=tmp_path)
    window = store.resolve_window("剪辑完成窗口")

    assert window["automation_id"] == "MessageBoxTip"
    assert "title" not in window


def test_asset_store_defaults_to_repo_assets_directory():
    store = AssetStore()

    assert store.root_dir == asset_store_module.DEFAULT_ASSET_ROOT
    assert (store.root_dir / "windows").exists()
    assert "window.main.record_software" in store.load_windows()
