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
        # 元素清单里允许保留 label 等说明性字段，但运行时只把真正的定位字段传给 UIA。
        criteria = {
            key: value
            for key, value in locator.items()
            if key not in {"page", "label", "module", "module_label", "description"}
        }
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
    def _visible_text_from_wrapper(wrapper) -> str:
        try:
            if hasattr(wrapper, "is_visible") and not wrapper.is_visible():
                return ""
        except Exception:
            return ""
        for getter in (
            lambda: wrapper.window_text(),
            lambda: getattr(wrapper.element_info, "name", ""),
        ):
            try:
                candidate = getter()
            except Exception:
                candidate = ""
            if candidate:
                return candidate
        return ""

    def _text_search_roots(self):
        roots = []
        if self.driver.main_window_wrapper is not None:
            roots.append(self.driver.main_window_wrapper)
        for getter in (
            lambda: self.driver.top_window(),
            lambda: self.driver.desktop.top_window(),
        ):
            try:
                candidate = getter()
                if hasattr(candidate, "wrapper_object"):
                    candidate = candidate.wrapper_object()
            except Exception:
                candidate = None
            if candidate is None:
                continue
            candidate_handle = getattr(candidate, "handle", None)
            if any(getattr(root, "handle", None) == candidate_handle for root in roots):
                continue
            roots.append(candidate)
        return roots

    def _iter_visible_texts_from_roots(self):
        seen = set()
        for root in self._text_search_roots():
            root_handle = getattr(root, "handle", None)
            if root_handle in seen:
                continue
            seen.add(root_handle)
            root_text = self._visible_text_from_wrapper(root)
            if root_text:
                yield root_text
            try:
                descendants = root.descendants()
            except Exception:
                descendants = []
            for descendant in descendants:
                candidate = self._visible_text_from_wrapper(descendant)
                if candidate:
                    yield candidate

    def assert_text_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            for candidate in self._iter_visible_texts_from_roots():
                if pattern.search(candidate):
                    self.logger.info("Found expected text: %s", text)
                    return
            time.sleep(0.5)

        samples = []
        for candidate in self._iter_visible_texts_from_roots():
            if candidate not in samples:
                samples.append(candidate)
            if len(samples) >= 20:
                break
        raise AssertionError(f"Text not visible in current app windows within {timeout}s: {text}. Visible samples: {samples}")

    def assert_text_not_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            found = False
            for candidate in self._iter_visible_texts_from_roots():
                if pattern.search(candidate):
                    found = True
                    break
            if not found:
                self.logger.info("Confirmed text disappeared: %s", text)
                return
            time.sleep(0.5)

        raise AssertionError(f"Text still visible in current app windows after {timeout}s: {text}")