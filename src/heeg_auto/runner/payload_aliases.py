from __future__ import annotations

PARAM_KEY_ALIASES = {
    "姓名": "patient_name",
    "患者姓名": "patient_name",
    "性别": "gender",
    "利手": "habit_hand",
    "病历号": "patient_id",
    "脑电号": "eeg_id",
    "备注": "note",
    "预期错误包含": "expect_error_contains",
    "设备类型": "device_type",
    "采样率": "sample_rate",
    "波特率": "baud_rate",
    "头盒数目": "head_box_number",
    "IP地址": "ip_address",
    "IP地址1": "ip_address_1",
    "IP地址2": "ip_address_2",
    "端口": "port",
    "设备名称": "device_name",
    "设备增益": "gain_value",
    "软件路径": "exe_path",
    "exe路径": "exe_path",
    "会话模式": "session_mode",
}

CONTEXT_KEY_ALIASES = {
    **PARAM_KEY_ALIASES,
    "变参值": "variant_value",
}
