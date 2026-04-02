from __future__ import annotations

from heeg_auto.runner.module_runner import ModuleRunner


class _FakeActions:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def resolve_action_name(self, action_name: str) -> str:
        return {
            "下拉选择": "select_combo",
            "断言窗口关闭": "assert_window_closed",
        }[action_name]

    def select_combo(self, **payload):
        self.calls.append(("select_combo", payload))

    def assert_window_closed(self, **payload):
        self.calls.append(("assert_window_closed", payload))


def test_module_runner_uses_named_assertion_group():
    runner = ModuleRunner()
    actions = _FakeActions()
    elements = {
        "采样率下拉框": {
            "label": "采样率下拉框",
            "page": "dialog",
            "automation_id": "SampleRates",
            "control_type": "ComboBox",
        },
        "设备设置标题": {
            "label": "设备设置标题",
            "page": "dialog",
            "title": "设备设置",
        },
    }
    module_definition = {
        "module_id": "device.settings",
        "module_label": "设备设置",
        "steps": [
            {
                "step_name": "选择采样率",
                "action": "下拉选择",
                "element": "采样率下拉框",
                "value": "${采样率}",
                "when_param": "采样率",
            }
        ],
        "assertions": {
            "设置成功": [
                {
                    "step_name": "设备设置窗口关闭",
                    "action": "断言窗口关闭",
                    "element": "设备设置标题",
                }
            ]
        },
    }
    params = {"sample_rate": "2000"}

    result = runner._run_module(actions, elements, module_definition, params, assertion_group="设置成功")

    assert result["status"] == "PASS"
    assert result["assertion_group"] == "设置成功"
    assert [item[0] for item in actions.calls] == ["select_combo", "assert_window_closed"]
    assert [item["stage"] for item in result["step_results"]] == ["步骤", "断言"]


def test_module_runner_still_repeats_step_for_list_param_values_when_needed():
    runner = ModuleRunner()
    actions = _FakeActions()
    elements = {
        "采样率下拉框": {
            "label": "采样率下拉框",
            "page": "dialog",
            "automation_id": "SampleRates",
            "control_type": "ComboBox",
        }
    }
    module_definition = {
        "module_id": "device.settings",
        "module_label": "设备设置",
        "steps": [
            {
                "step_name": "选择采样率",
                "action": "下拉选择",
                "element": "采样率下拉框",
                "value": "${采样率}",
                "when_param": "采样率",
            }
        ],
        "assertions": {},
    }
    params = {"sample_rate": ["1000", "2000", "4000"]}

    result = runner._run_module(actions, elements, module_definition, params, assertion_group=None)

    assert result["status"] == "PASS"
    assert [payload["value"] for _, payload in actions.calls] == ["1000", "2000", "4000"]
    assert len(result["step_results"]) == 3
