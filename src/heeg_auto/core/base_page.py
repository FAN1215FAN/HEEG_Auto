from __future__ import annotations

import re
import time

from pywinauto.findwindows import ElementNotFoundError

from heeg_auto.config.settings import ACTION_PAUSE_SECONDS, DEFAULT_TIMEOUT


class BasePage:
    def __init__(self, driver, logger, root=None) -> None:
        self.driver = driver
        self.logger = logger
        self.root = root

    @staticmethod
    def _criteria(locator: dict) -> dict:
        criteria = {key: value for key, value in locator.items() if key not in {"page"}}
        if "automation_id" in criteria:
            criteria["auto_id"] = criteria.pop("automation_id")
        return criteria

    def _resolve_root(self, locator: dict):
        if self.root is not None:
            return self.root
        page = locator.get("page")
        if page == "app":
            return None
        return self.driver.main_window

    def find(self, locator: dict, timeout: int = DEFAULT_TIMEOUT):
        criteria = self._criteria(locator)
        root = self._resolve_root(locator)
        deadline = time.time() + timeout
        last_error = None

        while time.time() < deadline:
            try:
                if root is None:
                    window_spec = self.driver.app.window(**criteria)
                    if window_spec.exists(timeout=0.5):
                        return window_spec
                else:
                    return root.child_window(**criteria).wrapper_object()
            except Exception as exc:  # pragma: no cover
                last_error = exc
            time.sleep(0.5)

        raise ElementNotFoundError(f"Unable to find control {criteria}: {last_error}")

    def click(self, locator: dict) -> None:
        control = self.find(locator)
        self.logger.info("Click control: %s", locator)
        control.click_input()
        time.sleep(ACTION_PAUSE_SECONDS)

    def input_text(self, locator: dict, value: str) -> None:
        control = self.find(locator)
        self.logger.info("Input text on %s -> %s", locator, value)
        control.set_focus()
        try:
            control.set_edit_text("")
            control.set_edit_text(value)
        except Exception:
            control.type_keys("^a{BACKSPACE}", set_foreground=True)
            control.type_keys(value, with_spaces=True, set_foreground=True)
        time.sleep(ACTION_PAUSE_SECONDS)

    def select_combo(self, locator: dict, value: str) -> None:
        control = self.find(locator)
        self.logger.info("Select combo %s -> %s", locator, value)
        try:
            control.select(value)
        except Exception:
            control.click_input()
            control.type_keys("^a{BACKSPACE}", set_foreground=True)
            control.type_keys(value, with_spaces=True, set_foreground=True)
            control.type_keys("{ENTER}", set_foreground=True)
        time.sleep(ACTION_PAUSE_SECONDS)

    def select_radio(self, locator: dict) -> None:
        control = self.find(locator)
        self.logger.info("Select radio: %s", locator)
        control.click_input()
        time.sleep(ACTION_PAUSE_SECONDS)

    def wait_closed(self, locator: dict, timeout: int = DEFAULT_TIMEOUT) -> None:
        criteria = self._criteria(locator)
        if self.root is not None:
            raise RuntimeError("wait_closed is only intended for top level windows.")

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                window = self.driver.app.window(**criteria)
                if not window.exists(timeout=0.5):
                    return
            except Exception:
                return
            time.sleep(0.5)
        raise TimeoutError(f"Window still exists after {timeout}s: {criteria}")

    @staticmethod
    def _iter_visible_texts(descendants):
        for descendant in descendants:
            try:
                if hasattr(descendant, "is_visible") and not descendant.is_visible():
                    continue
            except Exception:
                continue
            try:
                candidate = descendant.window_text()
            except Exception:
                candidate = ""
            if candidate:
                yield candidate

    def assert_text_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            for candidate in self._iter_visible_texts(self.driver.main_window_wrapper.descendants()):
                if pattern.search(candidate):
                    self.logger.info("Found expected text: %s", text)
                    return
            time.sleep(0.5)

        raise AssertionError(f"Text not visible in main window within {timeout}s: {text}")

    def assert_text_not_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            found = False
            for candidate in self._iter_visible_texts(self.driver.main_window_wrapper.descendants()):
                if pattern.search(candidate):
                    found = True
                    break
            if not found:
                self.logger.info("Confirmed text disappeared: %s", text)
                return
            time.sleep(0.5)

        raise AssertionError(f"Text still visible in main window after {timeout}s: {text}")
