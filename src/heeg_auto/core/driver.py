from __future__ import annotations

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

    def launch(self):
        ensure_artifact_dirs()
        self.logger.info("Launching application: %s", APP_PATH)
        self.app = Application(backend=UIA_BACKEND).start(str(APP_PATH))
        self.app.wait_cpu_usage_lower(threshold=5, timeout=MAIN_WINDOW_TIMEOUT)
        self.main_window = self._wait_for_main_window()
        self.main_window.wait("ready", timeout=MAIN_WINDOW_TIMEOUT)
        self.main_window_wrapper = self.main_window.wrapper_object()
        self.main_window_wrapper.set_focus()
        time.sleep(ACTION_PAUSE_SECONDS)
        return self.main_window

    def _wait_for_main_window(self):
        deadline = time.time() + MAIN_WINDOW_TIMEOUT
        last_error = None
        while time.time() < deadline:
            try:
                # 首版优先通过“可见 + 有标题 + 控件类型为 Window”识别主窗口，兼顾稳定性和简单性。
                window_spec = self.app.top_window()
                window = window_spec.wrapper_object()
                title = (window.window_text() or "").strip()
                if window.is_visible() and window.element_info.control_type == "Window" and title:
                    self.logger.info("Main window detected: %s", title)
                    return window_spec
            except Exception as exc:  # pragma: no cover
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

    def capture_failure_artifacts(
        self,
        case_name: str,
        step_name: str,
        timestamp: str,
        step_index: int | None = None,
    ) -> list[Path]:
        # 失败时尽量同时保留全屏、活动窗口和主窗口三类证据，兼容单屏和扩展屏场景。
        saved_paths: list[Path] = []
        case_part = self._safe_fragment(case_name)
        step_part = self._safe_fragment(step_name)
        index_part = f"step{step_index:02d}_" if step_index is not None else ""
        prefix = f"{case_part}_{index_part}{step_part}_{timestamp}"

        try:
            saved_paths.append(self.capture_full_screen(f"{prefix}_screen.png"))
        except Exception as exc:  # pragma: no cover
            self.logger.error("Failed to save full-screen screenshot: %s", exc)

        candidates = []
        try:
            candidates.append(("active", self.top_window()))
        except Exception as exc:  # pragma: no cover
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
            except Exception as exc:  # pragma: no cover
                self.logger.error("Failed to save %s window screenshot: %s", label, exc)

        return saved_paths

    def close(self) -> None:
        if not self.app:
            return
        try:
            self.top_window().close()
        except Exception:  # pragma: no cover
            pass
