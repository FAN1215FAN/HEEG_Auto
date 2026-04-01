from __future__ import annotations

from heeg_auto.runner.module_runner import ModuleRunner


class _FakeActions:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def resolve_action_name(self, action_name: str) -> str:
        return {
            "下拉选择": "select_combo",
        }[action_name]

    def select_combo(self, **payload):
        self.calls.append(("select_combo", payload))


def test_module_runner_repeats_step_for_list_param_values():
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
    params = {"sample_rate": ["1000", "2000", "4000"], "expect_status": "PASS"}

    result = runner._run_module(actions, elements, module_definition, params)

    assert result["status"] == "PASS"
    assert [payload["value"] for _, payload in actions.calls] == ["1000", "2000", "4000"]
    assert len(result["step_results"]) == 3
