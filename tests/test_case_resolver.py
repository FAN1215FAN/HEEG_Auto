from __future__ import annotations

from pathlib import Path

from heeg_auto.runner.case_resolver import detect_case_format, load_case_payload


def test_case_resolver_detects_v1_and_v2_formats(tmp_path: Path):
    v1_file = tmp_path / 'v1.yaml'
    v2_file = tmp_path / 'v2.yaml'
    v1_file.write_text(
        '用例编号: A\n用例名称: A\n模块链:\n  - 模块: 启动软件\n    参数:\n      会话模式: 自动\n',
        encoding='utf-8',
    )
    v2_file.write_text(
        '用例编号: B\n用例名称: B\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n',
        encoding='utf-8',
    )

    assert detect_case_format(v1_file) == 'v1'
    assert detect_case_format(v2_file) == 'v2'


def test_case_resolver_loads_v2_payload_with_default_labels(tmp_path: Path):
    v2_file = tmp_path / 'v2.yaml'
    v2_file.write_text(
        '用例编号: B\n用例名称: B\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n',
        encoding='utf-8',
    )

    payload = load_case_payload(v2_file)

    assert payload['case_format'] == 'v2'
    assert payload['module_chain_labels'] == ['V2步骤式']
    assert payload['steps'][0]['action'] == '启动应用'
