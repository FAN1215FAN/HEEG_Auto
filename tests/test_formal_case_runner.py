from __future__ import annotations

from heeg_auto.runner.formal_case_runner import FormalCaseRunner


def test_build_execution_plan_supports_multi_param_rows():
    runner = FormalCaseRunner()
    case_data = {
        "case_id": "设备设置_01",
        "case_name": "采样率校验",
        "loop_count": 2,
        "variant": {
            "module": "device.settings",
            "module_label": "设备设置",
            "params": [
                {"param": "device_type", "param_label": "设备类型"},
                {"param": "sample_rate", "param_label": "采样率"},
            ],
            "values": [
                {
                    "mapping": {"device_type": "Neusen HEEG", "sample_rate": "1000"},
                    "display_values": [
                        {"param": "device_type", "param_label": "设备类型", "value": "Neusen HEEG"},
                        {"param": "sample_rate", "param_label": "采样率", "value": "1000"},
                    ],
                },
                {
                    "mapping": {"device_type": "Neusen U32", "sample_rate": "2000"},
                    "display_values": [
                        {"param": "device_type", "param_label": "设备类型", "value": "Neusen U32"},
                        {"param": "sample_rate", "param_label": "采样率", "value": "2000"},
                    ],
                },
            ],
        },
    }

    plan = runner._build_execution_plan(case_data)

    assert len(plan) == 4
    assert plan[0]["execution_name"] == "采样率校验 | 设备类型=Neusen HEEG | 采样率=1000 | 第1轮"
    assert plan[1]["execution_name"] == "采样率校验 | 设备类型=Neusen HEEG | 采样率=1000 | 第2轮"
    assert plan[2]["variant"]["params"][0]["value"] == "Neusen U32"
    assert plan[2]["variant"]["params"][1]["value"] == "2000"


def test_build_execution_chain_resolves_named_variant_placeholders():
    runner = FormalCaseRunner()
    case_data = {
        "context": {
            "timestamp": "20260407160000",
            "variant_value": "${变参值}",
            "变参值": "${变参值}",
            "device_type": "${设备类型}",
            "设备类型": "${设备类型}",
            "sample_rate": "${采样率}",
            "采样率": "${采样率}",
        },
        "module_chain": [
            {
                "module": "device.settings",
                "params": {
                    "device_type": "${设备类型}",
                    "sample_rate": "${采样率}",
                    "ip_address": "192.168.1.123",
                },
                "assertion_group": "设置成功",
            }
        ],
    }
    execution = {
        "variant_params": [
            {"param": "device_type", "param_label": "设备类型", "value": "Neusen HEEG"},
            {"param": "sample_rate", "param_label": "采样率", "value": "1000"},
        ]
    }

    working_chain = runner._build_execution_chain(case_data, execution)

    assert working_chain[0]["params"]["device_type"] == "Neusen HEEG"
    assert working_chain[0]["params"]["sample_rate"] == "1000"
    assert working_chain[0]["params"]["ip_address"] == "192.168.1.123"


def test_run_case_delegates_to_v2_executor(monkeypatch, tmp_path):
    case_file = tmp_path / "v2_case.yaml"
    case_file.write_text(
        "用例编号: V2_001\n用例名称: V2\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n",
        encoding="utf-8",
    )

    runner = FormalCaseRunner()
    monkeypatch.setattr(
        runner.v2_case_loader,
        "load",
        lambda path: {
            "case_id": "V2_001",
            "case_name": "V2",
            "case_path": str(path),
            "context": {"timestamp": "20260409130000"},
            "steps": [{"step_name": "启动", "action": "启动应用", "params": {}, "assertions": []}],
        },
    )
    monkeypatch.setattr(
        runner.v2_executor,
        "run_case",
        lambda actions, case_data, progress_callback=None: {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "status": "PASS",
            "passed": True,
            "execution_results": [],
            "summary": {
                "planned_runs": 1,
                "executed_runs": 1,
                "passed_runs": 1,
                "failed_runs": 0,
                "interrupted_runs": 0,
                "not_run_runs": 0,
            },
        },
    )

    result = runner.run_case(case_file, raise_on_failure=False, close_after_run=False)

    assert result["case_id"] == "V2_001"
    assert result["status"] == "PASS"
    assert result["module_chain_labels"] == ["V2步骤式"]
