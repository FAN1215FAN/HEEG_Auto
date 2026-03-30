from __future__ import annotations


def open_create_patient(actions, elements) -> None:
    actions.click(elements["open_button"])
    actions.wait_for_window(elements["dialog_marker"])


def fill_basic_info(actions, elements, *, name: str, gender: str, habit_hand: str = "right_hand_radio") -> None:
    actions.input_text(elements["name_input"], name)
    actions.select_combo(elements["gender_combo"], gender)
    actions.select_radio(elements[habit_hand])


def fill_identifiers(actions, elements, *, patient_id: str, eeg_id: str, note: str = "") -> None:
    actions.input_text(elements["patient_id_input"], patient_id)
    actions.input_text(elements["eeg_id_input"], eeg_id)
    if note:
        actions.input_text(elements["note_input"], note)


def submit_create_patient(actions, elements) -> None:
    actions.click(elements["confirm_button"])


def validate_create_patient(actions, elements, *, patient_name: str, expect_status: str, expect_error_contains: str = "") -> None:
    if expect_status == "PASS":
        actions.assert_window_closed(elements["dialog_marker"])
        actions.assert_text_visible(patient_name)
        return

    actions.assert_exists(elements["dialog_marker"])
    if expect_error_contains:
        actions.assert_text_visible(expect_error_contains)
