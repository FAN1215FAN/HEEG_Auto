from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORT_FILE_NAMES = {"init.yaml", "cleanup.yaml"}


@dataclass
class DirectorySupportFiles:
    directory: Path
    init_file: Path | None
    cleanup_file: Path | None


class DirectoryLifecycleManager:
    def __init__(self, runner, stall_timeout_seconds: int = 60) -> None:
        self.runner = runner
        self.logger = runner.logger
        self.stall_timeout_seconds = stall_timeout_seconds
        self._current_support: DirectorySupportFiles | None = None
        self._entered = False
        self._needs_reset = False

    def prepare_for_case(self, case_path: str | Path) -> None:
        case_file = Path(case_path)
        support = self._resolve_support_files(case_file.parent)
        if self._current_support is None or self._current_support.directory != support.directory:
            self.finish()
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
        if self._current_support and self._current_support.cleanup_file:
            try:
                self._run_hook(self._current_support.cleanup_file, label="目录清理")
            except Exception as exc:
                self.logger.warning("directory.lifecycle cleanup failed %s | %s", self._current_support.directory, exc)
        if self._current_support:
            self._hard_reset(reason="目录结束清理")
        self._current_support = None
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
        if self._current_support.init_file is None:
            self._needs_reset = False
            return
        self._run_hook(self._current_support.init_file, label=f"目录恢复初始化:{reason}")
        self._entered = True
        self._needs_reset = False

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
