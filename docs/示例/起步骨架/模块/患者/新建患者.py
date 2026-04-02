from __future__ import annotations

from docs.examples.起步骨架.submodules.patient.fill_basic_info import fill_basic_info
from docs.examples.起步骨架.submodules.patient.fill_identifiers import fill_identifiers
from docs.examples.起步骨架.submodules.patient.submit_create_patient import submit_create_patient


class CreatePatientModule:
    """新建患者大模块样板。

    正式用例应该直接调用这个大模块，而不是继续平铺“单击 / 输入”。
    """

    module_id = "patient.create"
    module_label = "新建患者"

    def execute(self, actions, elements, params: dict) -> dict:
        actions.click(elements["open_button"])
        actions.wait_for_window(elements["dialog_marker"])

        fill_basic_info(
            actions,
            elements,
            name=params["name"],
            gender=params["gender"],
            habit_hand=params.get("habit_hand", "right_hand_radio"),
        )
        fill_identifiers(
            actions,
            elements,
            patient_id=params["patient_id"],
            eeg_id=params["eeg_id"],
            note=params.get("note", ""),
        )
        submit_create_patient(actions, elements)

        return {
            "module_id": self.module_id,
            "module_label": self.module_label,
            "expect_status": params.get("expect_status", "PASS"),
            "expect_error_contains": params.get("expect_error_contains", ""),
            "patient_name": params["name"],
        }

