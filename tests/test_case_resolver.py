from __future__ import annotations

from pathlib import Path

import pytest

from heeg_auto.runner.case_resolver import detect_case_format, load_case_payload


def test_case_resolver_only_accepts_step_cases(tmp_path: Path):
    invalid_file = tmp_path / "invalid.yaml"
    step_file = tmp_path / "step.yaml"
    invalid_file.write_text(
        "用例编号: A\n用例名称: A\n标签:\n  - smoke\n",
        encoding="utf-8",
    )
    step_file.write_text(
        "用例编号: B\n用例名称: B\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n",
        encoding="utf-8",
    )

    assert detect_case_format(step_file) == "step"
    with pytest.raises(ValueError, match="只支持步骤式 case"):
        detect_case_format(invalid_file)


def test_case_resolver_loads_step_payload_with_default_labels(tmp_path: Path):
    step_file = tmp_path / "step.yaml"
    step_file.write_text(
        "用例编号: B\n用例名称: B\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n",
        encoding="utf-8",
    )

    payload = load_case_payload(step_file)

    assert payload["case_format"] == "step"
    assert payload["module_chain_labels"] == ["步骤式"]
    assert payload["steps"][0]["action"] == "启动应用"
