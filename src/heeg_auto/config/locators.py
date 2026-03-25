from __future__ import annotations

from copy import deepcopy


CONTROL_MAP = {
    "main_window": {
        "page": "app",
        "control_type": "Window",
    },
    "create_patient_dialog": {
        "page": "main",
        "title": "创建患者",
    },
    "NewPatient": {
        "page": "main",
        "automation_id": "NewPatient",
        "control_type": "Button",
    },
    "PatientName": {
        "page": "dialog",
        "automation_id": "PatientName",
        "control_type": "Edit",
    },
    "PatientGender": {
        "page": "dialog",
        "automation_id": "PatientGender",
        "control_type": "ComboBox",
    },
    "PatientBirthDate": {
        "page": "dialog",
        "automation_id": "PatientBirthDate",
        "control_type": "Custom",
    },
    "PatientAge": {
        "page": "dialog",
        "automation_id": "PatientAge",
        "control_type": "Edit",
    },
    "PatientRightHand": {
        "page": "dialog",
        "automation_id": "PatientRightHand",
        "control_type": "RadioButton",
    },
    "PatientLeftHand": {
        "page": "dialog",
        "automation_id": "PatienLeftHand",
        "control_type": "RadioButton",
    },
    "PatientNoHabitHand": {
        "page": "dialog",
        "automation_id": "PatienNoHabitHand",
        "control_type": "RadioButton",
    },
    "PatientPairHand": {
        "page": "dialog",
        "automation_id": "PatienPairHand",
        "control_type": "RadioButton",
    },
    "PatientID": {
        "page": "dialog",
        "automation_id": "PatientID",
        "control_type": "Edit",
    },
    "PatientEEGID": {
        "page": "dialog",
        "automation_id": "PatientEEGID",
        "control_type": "Edit",
    },
    "PatientNote": {
        "page": "dialog",
        "automation_id": "PatientNote",
        "control_type": "Edit",
    },
    "Ok": {
        "page": "dialog",
        "title": "确定",
        "control_type": "Button",
    },
    "Cancel": {
        "page": "dialog",
        "title": "关闭",
        "control_type": "Button",
    },
}

CONTROL_ALIASES = {
    "创建患者": "create_patient_dialog",
    "新增": "NewPatient",
    "姓名": "PatientName",
    "性别": "PatientGender",
    "出生日期": "PatientBirthDate",
    "年龄": "PatientAge",
    "右利手": "PatientRightHand",
    "左利手": "PatientLeftHand",
    "无利手": "PatientNoHabitHand",
    "双利手": "PatientPairHand",
    "病历号": "PatientID",
    "脑电号": "PatientEEGID",
    "备注": "PatientNote",
    "确定": "Ok",
    "关闭": "Cancel",
}

LOCATOR_KEY_ALIASES = {
    "automationId": "automation_id",
    "auto_id": "automation_id",
    "name": "title",
    "visible_text": "title",
    "text": "title",
    "controlType": "control_type",
    "page_name": "page",
    "自动化ID": "automation_id",
    "控件类型": "control_type",
    "标题": "title",
    "名称": "title",
    "页面": "page",
}


def get_locator(name: str) -> dict:
    if name not in CONTROL_MAP:
        raise KeyError(f"Unknown locator: {name}")
    return deepcopy(CONTROL_MAP[name])


def normalize_locator(raw_locator: dict, default_page: str | None = None) -> dict:
    locator = {}
    for key, value in raw_locator.items():
        normalized_key = LOCATOR_KEY_ALIASES.get(key, key)
        locator[normalized_key] = value
    if default_page and "page" not in locator:
        locator["page"] = default_page
    return locator


def resolve_locator(target, default_page: str | None = None) -> dict:
    if isinstance(target, dict):
        return normalize_locator(deepcopy(target), default_page=default_page)

    if not isinstance(target, str):
        raise TypeError(f"Unsupported target type: {type(target)!r}")

    if target in CONTROL_MAP:
        return get_locator(target)

    if target in CONTROL_ALIASES:
        return get_locator(CONTROL_ALIASES[target])

    locator = {"title": target}
    if default_page:
        locator["page"] = default_page
    return locator
