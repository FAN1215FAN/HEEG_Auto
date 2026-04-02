from __future__ import annotations

import subprocess
import time
from pathlib import Path

from PIL import ImageGrab
from pywinauto import Application, Desktop

from heeg_auto.config.settings import (
    ACTION_PAUSE_SECONDS,
    APP_PATH,
    MAIN_WINDOW_TIMEOUT,
    SCREENSHOT_DIR,
    UIA_BACKEND,
    ensure_artifact_dirs,
)


class UIADriver:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.app: Application | None = None
        self.desktop = Desktop(backend=UIA_BACKEND)
        self.main_window = None
        self.main_window_wrapper = None
        self.current_app_path = APP_PATH

    def launch(self, exe_path: str | None = None) -> str:
        ensure_artifact_dirs()
        app_path = Path(exe_path) if exe_path else APP_PATH
        self.current_app_path = app_path
        if self.app and self.main_window_wrapper is not None:
            self.logger.info("Reuse existing application session.")
            return "reuse"
        attached = self._attach_existing(app_path)
        if attached:
            self.logger.info("Attached to existing application session.")
            return "attach"
        self.logger.info("Launching application: %s", app_path)
        self.app = Application(backend=UIA_BACKEND).start(str(app_path), wait_for_idle=False)
        self._wait_for_startup_stable()
        self._bind_main_window()
        self.main_window_wrapper.set_focus()
        time.sleep(ACTION_PAUSE_SECONDS)
        return "launch"

    def reuse_existing(self, exe_path: str | None = None) -> str:
        ensure_artifact_dirs()
        app_path = Path(exe_path) if exe_path else APP_PATH
        self.current_app_path = app_path
        if self.app and self.main_window_wrapper is not None:
            self.logger.info("Reuse existing application session.")
            return "reuse"
        attached = self._attach_existing(app_path)
        if attached:
            self.logger.info("Attached to existing application session.")
            return "attach"
        raise RuntimeError("要求复用已有应用，但未检测到可复用程序。")

    def _attach_existing(self, app_path: Path) -> bool:
        try:
            self.app = Application(backend=UIA_BACKEND).connect(path=str(app_path), timeout=5)
            self._bind_main_window()
            self.main_window_wrapper.set_focus()
            time.sleep(ACTION_PAUSE_SECONDS)
            return True
        except Exception:
            self.app = None
            self.main_window = None
            self.main_window_wrapper = None
            return False

    def _wait_for_startup_stable(self) -> None:
        try:
            self.app.wait_cpu_usage_lower(threshold=5, timeout=8)
            self.logger.info("Application CPU usage lowered below threshold.")
        except Exception as exc:
            self.logger.warning("Skipping CPU idle wait after timeout: %s", exc)

    def _bind_main_window(self) -> None:
        self.main_window = self._wait_for_main_window()
        self.main_window.wait("ready", timeout=MAIN_WINDOW_TIMEOUT)
        self.main_window_wrapper = self.main_window.wrapper_object()

    def _wait_for_main_window(self):
        deadline = time.time() + MAIN_WINDOW_TIMEOUT
        last_error = None
        while time.time() < deadline:
            try:
                window_spec = self.app.top_window()
                window = window_spec.wrapper_object()
                title = (window.window_text() or "").strip()
                if window.is_visible() and window.element_info.control_type == "Window" and title:
                    self.logger.info("Main window detected: %s", title)
                    return window_spec
            except Exception as exc:
                last_error = exc
            time.sleep(0.5)
        raise RuntimeError(f"Unable to detect main window within {MAIN_WINDOW_TIMEOUT}s: {last_error}")

    def top_window(self):
        if not self.app:
            raise RuntimeError("Application is not started yet.")
        return self.app.top_window().wrapper_object()

    @staticmethod
    def _safe_fragment(value: str | None) -> str:
        if not value:
            return "unknown"
        cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
        cleaned = cleaned.strip("_")
        return cleaned or "unknown"

    def capture_screenshot(self, file_name: str) -> Path:
        ensure_artifact_dirs()
        screenshot_path = SCREENSHOT_DIR / file_name
        target = self.top_window() if self.app else self.desktop.top_window()
        target.capture_as_image().save(screenshot_path)
        self.logger.info("Saved screenshot: %s", screenshot_path)
        return screenshot_path

    def capture_full_screen(self, file_name: str) -> Path:
        ensure_artifact_dirs()
        screenshot_path = SCREENSHOT_DIR / file_name
        image = ImageGrab.grab(all_screens=True)
        image.save(screenshot_path)
        self.logger.info("Saved full-screen screenshot: %s", screenshot_path)
        return screenshot_path

    def capture_window_screenshot(self, file_name: str, target=None) -> Path:
        ensure_artifact_dirs()
        screenshot_path = SCREENSHOT_DIR / file_name
        target = target or self.top_window()
        target.capture_as_image().save(screenshot_path)
        self.logger.info("Saved window screenshot: %s", screenshot_path)
        return screenshot_path

    def capture_failure_artifacts(self, case_name: str, step_name: str, timestamp: str, step_index: int | None = None) -> list[Path]:
        saved_paths: list[Path] = []
        case_part = self._safe_fragment(case_name)
        step_part = self._safe_fragment(step_name)
        index_part = f"step{step_index:02d}_" if step_index is not None else ""
        prefix = f"{case_part}_{index_part}{step_part}_{timestamp}"
        try:
            saved_paths.append(self.capture_full_screen(f"{prefix}_screen.png"))
        except Exception as exc:
            self.logger.error("Failed to save full-screen screenshot: %s", exc)
        candidates = []
        try:
            candidates.append(("active", self.top_window()))
        except Exception as exc:
            self.logger.error("Failed to resolve active window for screenshot: %s", exc)
        if self.main_window_wrapper is not None:
            candidates.append(("main", self.main_window_wrapper))
        seen_handles: set[int] = set()
        for label, candidate in candidates:
            try:
                handle = int(candidate.handle)
            except Exception:
                handle = None
            if handle is not None and handle in seen_handles:
                continue
            if handle is not None:
                seen_handles.add(handle)
            try:
                saved_paths.append(self.capture_window_screenshot(f"{prefix}_{label}.png", target=candidate))
            except Exception as exc:
                self.logger.error("Failed to save %s window screenshot: %s", label, exc)
        return saved_paths

    def force_close_running_app(self) -> None:
        process_name = self.current_app_path.name if self.current_app_path else APP_PATH.name
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/IM", process_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            self.logger.warning("Forced close issued for process: %s", process_name)
        except Exception as exc:
            self.logger.error("Failed to force close process %s: %s", process_name, exc)
        finally:
            self.app = None
            self.main_window = None
            self.main_window_wrapper = None
            self.current_app_path = APP_PATH

    def close(self) -> None:
        if not self.app:
            return
        try:
            self.top_window().close()
        except Exception:
            pass
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                if not self.app.is_process_running():
                    break
            except Exception:
                break
            time.sleep(0.5)
        else:
            self.force_close_running_app()
            return
        self.app = None
        self.main_window = None
        self.main_window_wrapper = None
        self.current_app_path = APP_PATH
