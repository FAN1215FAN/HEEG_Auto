from __future__ import annotations

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "src" / "heeg_auto" / "config"
APP_CONFIG_PATH = CONFIG_DIR / "app_config.yaml"
ASSERTION_GROUPS_PATH = CONFIG_DIR / "assertion_groups.yaml"


def _load_yaml_file(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"配置文件必须是字典结构：{path}")
    return payload


APP_CONFIG = _load_yaml_file(APP_CONFIG_PATH)
APP_PATH = Path(
    APP_CONFIG.get("软件路径")
    or APP_CONFIG.get("app_path")
    or "F:/neuracle/HEEG_project/HEEG/NSH-R/Neuracle.EEGRecorder.Viewer.HEEG.exe"
)
APP_PROCESS_NAME = APP_PATH.name
UIA_BACKEND = "uia"
DEFAULT_TIMEOUT = 15
MAIN_WINDOW_TIMEOUT = 30
MAIN_WINDOW_READY_TIMEOUT = 5
ACTION_PAUSE_SECONDS = 0.5
DEFAULT_STALL_TIMEOUT = 20

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
INSPECTOR_DIR = ARTIFACTS_DIR / "inspectors"
LOG_DIR = ARTIFACTS_DIR / "logs"
REPORT_DIR = ARTIFACTS_DIR / "reports"
SCREENSHOT_DIR = ARTIFACTS_DIR / "screenshots"
CASES_DIR = PROJECT_ROOT / "src" / "heeg_auto" / "cases"
DEFAULT_ENVIRONMENT_MODE = "reuse_per_suite"

DEFAULT_CASE_PATH = CASES_DIR / "患者检查管理" / "患者管理" / "新建患者_正常创建.yaml"


def ensure_artifact_dirs() -> None:
    for directory in (INSPECTOR_DIR, LOG_DIR, REPORT_DIR, SCREENSHOT_DIR):
        directory.mkdir(parents=True, exist_ok=True)


