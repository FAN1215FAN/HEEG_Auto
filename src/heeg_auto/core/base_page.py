from __future__ import annotations

import re
import time
from typing import Any

from pywinauto import mouse
from pywinauto.findwindows import ElementNotFoundError

from heeg_auto.config.settings import ACTION_PAUSE_SECONDS, DEFAULT_TIMEOUT
from heeg_auto.core.duration_utils import parse_duration_seconds

_DURATION_TOKEN_PATTERN = re.compile(r"(?<!\d)(\d{2}:\d{2}:\d{2})(?!\d)")


class BasePage:
    def __init__(self, driver, logger, root=None) -> None:
        self.driver = driver
        self.logger = logger
        self.root = root

    @staticmethod
    def _criteria(locator: dict) -> dict:
        criteria = {
            key: value
            for key, value in locator.items()
            if key not in {"page", "label", "module", "module_label", "description", "aliases", "interaction_calibration"}
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

    def _root_candidates(self, locator: dict):
        root = self._resolve_root(locator)
        if root is None:
            return [None]

        candidates = []

        def push(candidate):
            if candidate is None:
                return
            if hasattr(candidate, "wrapper_object"):
                try:
                    candidate = candidate.wrapper_object()
                except Exception:
                    return
            handle = getattr(candidate, "handle", None)
            if any(getattr(existing, "handle", None) == handle for existing in candidates):
                return
            candidates.append(candidate)

        push(root)
        if self.root is not None:
            main_window = getattr(self.driver, "main_window", None)
            main_wrapper = getattr(self.driver, "main_window_wrapper", None)
            root_handle = getattr(root, "handle", None)
            main_handles = {getattr(main_window, "handle", None), getattr(main_wrapper, "handle", None)}
            if root_handle not in main_handles:
                return [self.root]
        push(getattr(self.driver, "main_window_wrapper", None))
        app = getattr(self.driver, "app", None)
        if app is not None:
            try:
                for candidate in app.windows():
                    push(candidate)
            except Exception:
                pass
        for getter in (self.driver.top_window, lambda: self.driver.desktop.top_window()):
            try:
                push(getter())
            except Exception:
                continue
        return candidates or [root]

    @staticmethod
    def _criteria_candidates(criteria: dict) -> list[dict]:
        candidates = [criteria]
        control_type = criteria.get("control_type")
        auto_id = criteria.get("auto_id")
        if not control_type:
            return candidates

        normalized = str(control_type).strip().lower()
        if normalized in {"edit", "textbox", "text box"} and auto_id:
            for variant in ("Edit", "TextBox"):
                if control_type != variant:
                    alt = dict(criteria)
                    alt["control_type"] = variant
                    candidates.append(alt)
            alt = dict(criteria)
            alt.pop("control_type", None)
            candidates.append(alt)
        return candidates

    @staticmethod
    def _matches_candidate(wrapper, candidate: dict) -> bool:
        info = getattr(wrapper, "element_info", None)
        if info is None:
            return False
        for key, expected in candidate.items():
            if key == "auto_id":
                actual = getattr(info, "automation_id", "")
            elif key == "control_type":
                actual = getattr(info, "control_type", "")
            elif key == "title":
                actual = getattr(info, "name", "") or ""
            else:
                actual = getattr(info, key, "")
            if str(actual) != str(expected):
                return False
        return True

    def _find_in_descendants(self, root, candidate: dict):
        try:
            descendants = root.descendants()
        except Exception:
            return None
        for descendant in descendants:
            try:
                if self._matches_candidate(descendant, candidate):
                    self.logger.info("Fallback descendant match for %s", candidate)
                    return descendant
            except Exception:
                continue
        return None

    def find(self, locator: dict, timeout: int = DEFAULT_TIMEOUT):
        criteria = self._criteria(locator)
        deadline = time.time() + timeout
        last_error = None

        while time.time() < deadline:
            for candidate in self._criteria_candidates(criteria):
                if candidate.get("control_type") == "Window":
                    try:
                        if self.driver.app is not None:
                            window_spec = self.driver.app.window(**candidate)
                            if window_spec.exists(timeout=0.5):
                                return window_spec.wrapper_object()
                    except Exception as exc:
                        last_error = exc
            for root in self._root_candidates(locator):
                for candidate in self._criteria_candidates(criteria):
                    try:
                        if root is None:
                            window_spec = self.driver.app.window(**candidate)
                            if window_spec.exists(timeout=0.5):
                                return window_spec
                        else:
                            try:
                                if self._matches_candidate(root, candidate):
                                    return root
                                if hasattr(root, "child_window"):
                                    return root.child_window(**candidate).wrapper_object()
                                raise AttributeError(f"{type(root).__name__} object has no attribute 'child_window'")
                            except Exception as exc:
                                last_error = exc
                                fallback = self._find_in_descendants(root, candidate)
                                if fallback is not None:
                                    return fallback
                    except Exception as exc:
                        last_error = exc
            time.sleep(0.5)

        raise ElementNotFoundError(f"Unable to find control {criteria}: {last_error}")

    def find_all(self, locator: dict) -> list:
        criteria = self._criteria(locator)
        results = []
        seen_handles: set[int | None] = set()
        for root in self._root_candidates(locator):
            if root is None:
                continue
            try:
                descendants = root.descendants()
            except Exception:
                descendants = []
            for descendant in descendants:
                try:
                    if not self._matches_candidate(descendant, criteria):
                        continue
                except Exception:
                    continue
                handle = getattr(descendant, "handle", None)
                if handle in seen_handles:
                    continue
                seen_handles.add(handle)
                results.append(descendant)
        return results

    def click(self, locator: dict) -> None:
        control = self.find(locator)
        self.logger.info("Click control: %s", locator)
        control.click_input()
        time.sleep(ACTION_PAUSE_SECONDS)

    def double_click(self, locator: dict) -> None:
        control = self.find(locator)
        self.logger.info("Double click control: %s", locator)
        try:
            control.double_click_input()
        except Exception:
            control.click_input(double=True)
        time.sleep(ACTION_PAUSE_SECONDS)

    def right_click(self, locator: dict) -> None:
        control = self.find(locator)
        self.logger.info("Right click control: %s", locator)
        try:
            control.right_click_input()
        except Exception:
            control.click_input(button="right")
        time.sleep(ACTION_PAUSE_SECONDS)

    def click_point(self, x: int, y: int, button: str = "left", double: bool = False) -> None:
        self.logger.info("Click point: button=%s double=%s coords=(%s,%s)", button, double, x, y)
        if double:
            mouse.double_click(button=button, coords=(x, y))
        elif button == "right":
            mouse.right_click(coords=(x, y))
        else:
            mouse.click(button=button, coords=(x, y))
        time.sleep(ACTION_PAUSE_SECONDS)

    def drag_point(self, start_x: int, start_y: int, end_x: int, end_y: int, button: str = "left") -> None:
        self.logger.info(
            "Drag point: button=%s start=(%s,%s) end=(%s,%s)",
            button,
            start_x,
            start_y,
            end_x,
            end_y,
        )
        mouse.press(button=button, coords=(start_x, start_y))
        mouse.move(coords=(end_x, end_y))
        mouse.release(button=button, coords=(end_x, end_y))
        time.sleep(ACTION_PAUSE_SECONDS)

    @staticmethod
    def rectangle_from_wrapper(wrapper) -> tuple[int, int, int, int]:
        rect = wrapper.rectangle()
        return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)

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

    def set_checkbox(self, locator: dict, value: Any) -> None:
        control = self.find(locator)
        expected = self._normalize_checkbox_value(value)
        current = self._checkbox_state(control)
        self.logger.info("Set checkbox %s -> %s (current=%s)", locator, expected, current)
        if current is None:
            control.click_input()
        elif current != expected:
            control.click_input()
        if self._checkbox_state(control) not in {None, expected}:
            raise AssertionError(f"Checkbox state did not change as expected: {locator} -> {expected}")
        time.sleep(ACTION_PAUSE_SECONDS)

    @staticmethod
    def _normalize_checkbox_value(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "是", "选中", "勾选", "开启", "开"}:
            return True
        if normalized in {"false", "0", "no", "n", "否", "未选中", "取消勾选", "取消选中", "关闭", "关"}:
            return False
        raise ValueError(f"无法解析 CheckBox 目标值: {value}")

    @staticmethod
    def _checkbox_state(control) -> bool | None:
        for getter in (
            lambda: control.get_toggle_state(),
            lambda: control.get_check_state(),
            lambda: control.toggle_state(),
        ):
            try:
                state = getter()
            except Exception:
                continue
            if state in {0, False}:
                return False
            if state in {1, True, 2}:
                return True
        return None

    def wait_closed(self, locator: dict, timeout: int = DEFAULT_TIMEOUT) -> None:
        criteria = self._criteria(locator)
        if self.root is not None:
            raise RuntimeError("wait_closed 只用于顶层窗口。")

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                window = self.driver.app.window(**criteria)
                if not window.exists(timeout=0.5):
                    return
            except Exception:
                return
            time.sleep(0.5)
        raise TimeoutError(f"窗口在 {timeout}s 后仍未关闭: {criteria}")

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
        if self.root is not None:
            return [self.root]

        roots = []

        def push(candidate):
            if candidate is None:
                return
            if hasattr(candidate, "wrapper_object"):
                try:
                    candidate = candidate.wrapper_object()
                except Exception:
                    return
            candidate_handle = getattr(candidate, "handle", None)
            if any(getattr(root, "handle", None) == candidate_handle for root in roots):
                return
            roots.append(candidate)

        if self.driver.main_window_wrapper is not None:
            push(self.driver.main_window_wrapper)
        app = getattr(self.driver, "app", None)
        if app is not None:
            try:
                for candidate in app.windows():
                    push(candidate)
            except Exception:
                pass
        for getter in (
            lambda: self.driver.top_window(),
            lambda: self.driver.desktop.top_window(),
        ):
            try:
                candidate = getter()
            except Exception:
                candidate = None
            push(candidate)
        return roots

    def iter_visible_texts(self):
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

    def collect_visible_texts(self) -> list[str]:
        return list(self.iter_visible_texts())

    def assert_text_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            for candidate in self.iter_visible_texts():
                if pattern.search(candidate):
                    self.logger.info("Matched text '%s' with candidate '%s'", text, candidate)
                    return
            time.sleep(0.5)
        raise AssertionError(f"Text not visible after {timeout}s: {text}")

    def assert_text_not_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        pattern = re.compile(re.escape(text))

        while time.time() < deadline:
            if not any(pattern.search(candidate) for candidate in self.iter_visible_texts()):
                return
            time.sleep(0.5)
        raise AssertionError(f"Text still visible after {timeout}s: {text}")

    def assert_duration_in_range(self, min_duration: str, max_duration: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        min_seconds = self._duration_to_seconds(min_duration, field_name="min_duration")
        max_seconds = self._duration_to_seconds(max_duration, field_name="max_duration")
        if max_seconds < min_seconds:
            raise ValueError(f"max_duration must be >= min_duration: {min_duration} ~ {max_duration}")

        deadline = time.time() + timeout
        observed: set[str] = set()
        while time.time() < deadline:
            for candidate in self.iter_visible_texts():
                for token in _DURATION_TOKEN_PATTERN.findall(candidate):
                    observed.add(token)
                    seconds = self._duration_to_seconds(token, field_name="observed_duration")
                    if min_seconds <= seconds <= max_seconds:
                        self.logger.info(
                            "Matched duration '%s' within range %s~%s from candidate '%s'",
                            token,
                            min_duration,
                            max_duration,
                            candidate,
                        )
                        return
            time.sleep(0.5)
        observed_text = ", ".join(sorted(observed)) if observed else "<none>"
        raise AssertionError(
            f"No duration within range after {timeout}s: {min_duration}~{max_duration}; observed={observed_text}"
        )

    def assert_control_enabled(self, locator: dict, timeout: int = DEFAULT_TIMEOUT) -> None:
        deadline = time.time() + timeout
        last_error = None
        last_state = None
        lookup_timeout = min(timeout, 1)

        while time.time() < deadline:
            try:
                control = self.find(locator, timeout=lookup_timeout)
                last_state = self._is_control_enabled(control)
                if last_state:
                    self.logger.info("Control enabled: %s", locator)
                    return
            except Exception as exc:
                last_error = exc
            time.sleep(0.5)

        detail = f" last_error={last_error}" if last_error else ""
        raise AssertionError(f"Control not enabled after {timeout}s: {locator}; last_state={last_state}.{detail}")

    @staticmethod
    def _duration_to_seconds(value: str, field_name: str) -> float:
        return parse_duration_seconds(value, field_name=field_name)

    @staticmethod
    def _is_control_enabled(control) -> bool | None:
        for getter in (
            lambda: control.is_enabled(),
            lambda: control.is_enabled,
            lambda: getattr(control.element_info, "enabled", None),
        ):
            try:
                state = getter()
            except Exception:
                continue
            if isinstance(state, bool):
                return state
            if state in {0, 1}:
                return bool(state)
        return None
