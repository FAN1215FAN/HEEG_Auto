from __future__ import annotations

from time import perf_counter

from heeg_auto.runner.exceptions import ModuleExecutionError
from heeg_auto.submodules.patient import (
    fill_basic_info,
    fill_identifiers,
    open_create_patient,
    submit_create_patient,
    validate_create_patient,
)


class CreatePatientModule:
    module_id = "patient.create"
    module_label = "新建患者"

    def execute(self, actions, elements, params: dict) -> dict:
        submodule_results: list[dict] = []

        def run_submodule(submodule_name: str, func, **kwargs):
            started = perf_counter()
            try:
                func(actions, elements, **kwargs)
                submodule_results.append(
                    {
                        "submodule": submodule_name,
                        "status": "PASS",
                        "duration_seconds": round(perf_counter() - started, 3),
                        "error_summary": "",
                    }
                )
            except Exception as exc:
                submodule_results.append(
                    {
                        "submodule": submodule_name,
                        "status": "FAIL",
                        "duration_seconds": round(perf_counter() - started, 3),
                        "error_summary": str(exc),
                    }
                )
                raise ModuleExecutionError(
                    module_id=self.module_id,
                    module_label=self.module_label,
                    submodule=submodule_name,
                    message=str(exc),
                    submodule_results=submodule_results,
                ) from exc

        run_submodule("open_create_patient", open_create_patient)
        run_submodule(
            "fill_basic_info",
            fill_basic_info,
            name=params["name"],
            gender=params["gender"],
            habit_hand=params.get("habit_hand", "right_hand_radio"),
        )
        run_submodule(
            "fill_identifiers",
            fill_identifiers,
            patient_id=params["patient_id"],
            eeg_id=params["eeg_id"],
            note=params.get("note", ""),
        )
        run_submodule("submit_create_patient", submit_create_patient)
        run_submodule(
            "validate_create_patient",
            validate_create_patient,
            patient_name=params["name"],
            expect_status=params.get("expect_status", "PASS"),
            expect_error_contains=params.get("expect_error_contains", ""),
        )

        return {
            "module_id": self.module_id,
            "module_label": self.module_label,
            "status": "PASS",
            "expected_status": params.get("expect_status", "PASS"),
            "patient_name": params["name"],
            "submodule_results": submodule_results,
        }
