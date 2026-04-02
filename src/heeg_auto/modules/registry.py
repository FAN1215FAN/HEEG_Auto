from __future__ import annotations

from heeg_auto.config.settings import MODULES_DIR

MODULE_FILE_REGISTRY = {
    "system.launch": MODULES_DIR / "system" / "launch_application.yaml",
    "patient.create": MODULES_DIR / "patient" / "create_patient.yaml",
    "device.settings": MODULES_DIR / "device" / "device_settings.yaml",
}

MODULE_NAME_ALIASES = {
    "启动软件": "system.launch",
    "system.launch": "system.launch",
    "新建患者": "patient.create",
    "patient.create": "patient.create",
    "设备设置": "device.settings",
    "device.settings": "device.settings",
}

