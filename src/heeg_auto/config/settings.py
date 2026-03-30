from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_PATH = Path('F:/neuracle/HEEG_project/HEEG/NSH-R/Neuracle.EEGRecorder.Viewer.HEEG.exe')
APP_PROCESS_NAME = APP_PATH.name
UIA_BACKEND = "uia"
DEFAULT_TIMEOUT = 15
MAIN_WINDOW_TIMEOUT = 30
ACTION_PAUSE_SECONDS = 0.5

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
INSPECTOR_DIR = ARTIFACTS_DIR / "inspectors"
LOG_DIR = ARTIFACTS_DIR / "logs"
REPORT_DIR = ARTIFACTS_DIR / "reports"
SCREENSHOT_DIR = ARTIFACTS_DIR / "screenshots"
ELEMENTS_DIR = PROJECT_ROOT / "src" / "heeg_auto" / "elements"
MODULES_DIR = PROJECT_ROOT / "src" / "heeg_auto" / "modules"
LEGACY_DIR = PROJECT_ROOT / "src" / "heeg_auto" / "legacy"

DEFAULT_CASE_PATH = PROJECT_ROOT / "src" / "heeg_auto" / "cases" / "patient" / "TC_PATIENT_001.yaml"


def ensure_artifact_dirs() -> None:
    for directory in (INSPECTOR_DIR, LOG_DIR, REPORT_DIR, SCREENSHOT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
