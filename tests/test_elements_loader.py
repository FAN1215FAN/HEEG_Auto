from __future__ import annotations

from heeg_auto.elements import ElementStore
from heeg_auto.config.settings import ELEMENTS_DIR


def test_element_store_loads_create_patient_module():
    elements = ElementStore(ELEMENTS_DIR).load("patient.create")

    assert elements["open_button"]["automation_id"] == "NewPatient"
    assert elements["name_input"]["automation_id"] == "PatientName"
    assert elements["confirm_button"]["title"] == "确定"
