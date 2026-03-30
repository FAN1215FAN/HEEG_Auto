from __future__ import annotations

from heeg_auto.config.settings import MODULES_DIR

MODULE_FILE_REGISTRY = {
    "patient.create": MODULES_DIR / "patient" / "create_patient.yaml",
}

MODULE_NAME_ALIASES = {
    "新建患者": "patient.create",
    "patient.create": "patient.create",
}
