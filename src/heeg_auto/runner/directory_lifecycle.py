from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from heeg_auto.config.settings import CASES_DIR, DEFAULT_ENVIRONMENT_MODE, DEFAULT_STALL_TIMEOUT

SUITE_SUPPORT_FILE_NAMES = {"suite_setup.yaml", "suite_cleanup.yaml"}
DIRECTORY_SUPPORT_FILE_NAMES = {"init.yaml", "cleanup.yaml"}
SUPPORT_FILE_NAMES = DIRECTORY_SUPPORT_FILE_NAMES | SUITE_SUPPORT_FILE_NAMES
ENVIRONMENT_MODE_ALIASES = {
    "reuse_per_suite": "reuse_per_suite",
    "suite": "reuse_per_suite",
    "按套件复用": "reuse_per_suite",
    "reset_per_directory": "reset_per_directory",
    "directory": "reset_per_directory",
    "按目录重置": "reset_per_directory",
}


@dataclass
class DirectorySupportFiles:
    directory: Path
    init_file: Path | None
    cleanup_file: Path | None


@dataclass
class SuiteSupportFiles:
    setup_file: Path | None
    cleanup_file: Path | None


class DirectoryLifecycleManager:
    def __init__(
        self,
        runner,
        stall_timeout_seconds: int = DEFAULT_STALL_TIMEOUT,
        environment_mode: str = DEFAULT_ENVIRONMENT_MODE,
        case_root: Path | None = None,
    ) -> None:
        self.runner = runner
        self.logger = runner.logger
        self.stall_timeout_seconds = stall_timeout_seconds
        self.environment_mode = self._normalize_environment_mode(environment_mode)
        self.case_root = Path(case_root) if case_root is not None else CASES_DIR
        self._suite_support = self._resolve_suite_support_files(self.case_root)
        self._current_support: DirectorySupportFiles | None = None
        self._suite_started = False
        self._entered = False
        self._needs_reset = False

    def prepare_for_case(self, case_path: str | Path) -> None:
        case_file = Path(case_path)
        self._ensure_suite_started()
        support = self._resolve_support_files(case_file.parent)
        if self._current_support is None or self._current_support.directory != support.directory:
            if self._current_support is not None:
                self._leave_directory(reason="切换目录")
            self._current_support = support
            self._entered = False
            self._needs_reset = False
        if support.init_file is None:
            return
        if not self._entered:
            self._run_hook(support.init_file, label="目录初始化")
            self._entered = True
            return
        if self._needs_reset or not self._is_ui_ready():
            reason = "前序 case 失败后恢复" if self._needs_reset else "界面状态校验未通过"
            self.logger.warning("directory.lifecycle recover %s | %s", support.directory, reason)
            self._recover_environment(reason=reason)

    def record_case_result(self, case_path: str | Path, result: dict[str, Any]) -> None:
        support = self._resolve_support_files(Path(case_path).parent)
        if self._current_support is None or self._current_support.directory != support.directory:
            return
        if result.get("status") in {"FAIL", "INTERRUPTED"}:
            self._needs_reset = True

    def finish(self) -> None:
        if self._current_support is not None:
            self._leave_directory(reason="套件结束")
        self._leave_suite(reason="套件结束")
        self._current_support = None
        self._suite_started = False
        self._entered = False
        self._needs_reset = False

    def _recover_environment(self, reason: str) -> None:
        if self._current_support is None:
            return
        if self._current_support.cleanup_file:
            try:
                self._run_hook(self._current_support.cleanup_file, label=f"目录恢复清理:{reason}")
            except Exception as exc:
                self.logger.warning("directory.lifecycle recover cleanup failed %s | %s", self._current_support.directory, exc)
        self._hard_reset(reason=reason)
        if self._suite_support.setup_file is not None:
            self._run_hook(self._suite_support.setup_file, label=f"套件恢复初始化:{reason}")
            self._suite_started = True
        if self._current_support.init_file is None:
            self._needs_reset = False
            return
        self._run_hook(self._current_support.init_file, label=f"目录恢复初始化:{reason}")
        self._entered = True
        self._needs_reset = False

    def _ensure_suite_started(self) -> None:
        if self._suite_started:
            return
        if self._suite_support.setup_file is not None:
            self._run_hook(self._suite_support.setup_file, label="套件初始化")
        self._suite_started = True

    def _leave_directory(self, reason: str) -> None:
        if self._current_support and self._current_support.cleanup_file:
            try:
                self._run_hook(self._current_support.cleanup_file, label=f"目录清理:{reason}")
            except Exception as exc:
                self.logger.warning("directory.lifecycle cleanup failed %s | %s", self._current_support.directory, exc)
        if self.environment_mode == "reset_per_directory" and self._current_support is not None:
            self._hard_reset(reason=reason)
        self._entered = False
        self._needs_reset = False

    def _leave_suite(self, reason: str) -> None:
        if not self._suite_started:
            return
        if self._suite_support.cleanup_file is not None:
            try:
                self._run_hook(self._suite_support.cleanup_file, label=f"套件清理:{reason}")
            except Exception as exc:
                self.logger.warning("directory.lifecycle suite cleanup failed %s | %s", self.case_root, exc)

    def _run_hook(self, hook_path: Path, label: str) -> None:
        self.logger.info("directory.lifecycle %s %s", label, hook_path)
        result = self.runner.run_case(
            hook_path,
            raise_on_failure=False,
            close_after_run=False,
            stall_timeout_seconds=self.stall_timeout_seconds,
        )
        if not result.get("passed", False):
            raise RuntimeError(result.get("error_summary") or f"{label} 执行失败：{hook_path}")

    def _hard_reset(self, reason: str) -> None:
        driver = getattr(self.runner, "driver", None)
        if driver is None:
            return
        self.logger.info("directory.lifecycle hard reset | %s", reason)
        try:
            driver.force_close_running_app()
        except Exception as exc:
            self.logger.warning("directory.lifecycle hard reset failed | %s | %s", reason, exc)

    def _is_ui_ready(self) -> bool:
        driver = self.runner.driver
        if driver.app is None or driver.main_window_wrapper is None:
            return False
        try:
            main_window = driver.main_window_wrapper
            return bool(main_window.is_visible())
        except Exception:
            return False

    @staticmethod
    def _resolve_support_files(directory: Path) -> DirectorySupportFiles:
        init_file = directory / "init.yaml"
        cleanup_file = directory / "cleanup.yaml"
        return DirectorySupportFiles(
            directory=directory,
            init_file=init_file if init_file.exists() else None,
            cleanup_file=cleanup_file if cleanup_file.exists() else None,
        )

    @staticmethod
    def _resolve_suite_support_files(case_root: Path) -> SuiteSupportFiles:
        setup_file = case_root / "suite_setup.yaml"
        cleanup_file = case_root / "suite_cleanup.yaml"
        return SuiteSupportFiles(
            setup_file=setup_file if setup_file.exists() else None,
            cleanup_file=cleanup_file if cleanup_file.exists() else None,
        )

    @staticmethod
    def _normalize_environment_mode(raw_mode: str) -> str:
        normalized = ENVIRONMENT_MODE_ALIASES.get(str(raw_mode).strip(), "")
        if not normalized:
            raise ValueError(f"不支持的环境模式：{raw_mode}")
        return normalized
