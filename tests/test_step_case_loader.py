from __future__ import annotations

from pathlib import Path

from heeg_auto.runner.step_case_loader import StepCaseLoader


def test_step_case_loader_supports_recommended_structure_and_multi_param_variant(tmp_path: Path):
    case_file = tmp_path / "step_case.yaml"
    case_file.write_text(
        """
用例编号: STEP_DEVICE_001
用例名称: 设备设置_步骤式
标签:
  - device
变参:
  参数:
    - 设备类型
    - 采样率
  候选值:
    - [Neusen HEEG, 1000]
    - [Neusen U32, 2000]
循环次数: 2
失败即停: 否
步骤:
  - 名称: 打开设备设置窗口
    窗口: 患者主界面
    按钮: 设备设置
    断言: 设备设置窗口已出现
  - 名称: 填写设备设置表单
    窗口: 设备设置
    参数:
      设备类型: ${设备类型}
      采样率: ${采样率}
      IP地址1: 192.168.1.123
  - 名称: 保存设备设置
    窗口: 设备设置
    按钮: 确定
    断言:
      - 设备设置已关闭
""".strip(),
        encoding="utf-8",
    )

    payload = StepCaseLoader().load(case_file)

    assert payload["case_id"] == "STEP_DEVICE_001"
    assert payload["loop_count"] == 2
    assert payload["variant"]["params"][0] == {"param": "device_type", "param_label": "设备类型"}
    assert payload["variant"]["values"][1]["mapping"]["sample_rate"] == "2000"
    assert payload["steps"][0]["button"] == "设备设置"
    assert payload["steps"][1]["field_params"]["设备类型"] == "${设备类型}"
    assert payload["steps"][1]["field_params"]["IP地址1"] == "192.168.1.123"
    assert payload["steps"][2]["assertions"] == ["设备设置已关闭"]
