from __future__ import annotations

from heeg_auto.config.settings import ELEMENTS_DIR
from heeg_auto.elements import ElementStore


def test_element_store_loads_create_patient_module():
    elements = ElementStore(ELEMENTS_DIR).load("patient.create")

    assert elements["open_button"]["automation_id"] == "NewPatient"
    assert elements["name_input"]["automation_id"] == "PatientName"
    assert elements["confirm_button"]["title"] == "确定"


def test_element_store_loads_device_settings_module():
    elements = ElementStore(ELEMENTS_DIR).load("device.settings")

    assert elements["open_button"]["automation_id"] == "SetDeviceSetting"
    assert elements["device_type_combo"]["automation_id"] == "DeviceTypes"
    assert elements["ip_address_input"]["control_type"] == "Edit"
    assert elements["confirm_button"]["title"] == "确定"


def test_element_store_supports_business_aliases():
    elements = ElementStore(ELEMENTS_DIR).load("patient.create")

    assert ElementStore.resolve_reference(elements, "左手")["automation_id"] == "PatienLeftHand"
    assert ElementStore.resolve_reference(elements, "右利手")["automation_id"] == "PatientRightHand"
