from __future__ import annotations


def fill_identifiers(actions, elements, *, patient_id: str, eeg_id: str, note: str = "") -> None:
    """填写病历号、脑电号和备注。"""

    actions.input_text(elements["patient_id_input"], patient_id)
    actions.input_text(elements["eeg_id_input"], eeg_id)
    if note:
        actions.input_text(elements["note_input"], note)
