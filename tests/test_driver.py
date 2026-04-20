from __future__ import annotations

from heeg_auto.core.driver import UIADriver


class _Logger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message, *args) -> None:
        self.warnings.append(message % args if args else message)


class _WindowSpec:
    def __init__(self, wrapper, wait_error: Exception | None = None) -> None:
        self._wrapper = wrapper
        self._wait_error = wait_error

    def wait(self, *_args, **_kwargs) -> None:
        if self._wait_error is not None:
            raise self._wait_error

    def wrapper_object(self):
        return self._wrapper


def test_bind_main_window_continues_when_ready_wait_times_out(monkeypatch):
    wrapper = object()
    logger = _Logger()
    driver = object.__new__(UIADriver)
    driver.logger = logger
    driver.main_window = None
    driver.main_window_wrapper = None

    window_spec = _WindowSpec(wrapper=wrapper, wait_error=TimeoutError("ready timeout"))
    monkeypatch.setattr(driver, "_wait_for_main_window", lambda: window_spec)

    driver._bind_main_window()

    assert driver.main_window is window_spec
    assert driver.main_window_wrapper is wrapper
    assert logger.warnings == ["Main window ready wait skipped after timeout: ready timeout"]


def test_focus_main_window_logs_warning_instead_of_raising():
    logger = _Logger()

    class _Wrapper:
        def set_focus(self) -> None:
            raise RuntimeError("focus failed")

    driver = object.__new__(UIADriver)
    driver.logger = logger
    driver.main_window_wrapper = _Wrapper()

    driver._focus_main_window()

    assert logger.warnings == ["Unable to focus main window, continue without focus: focus failed"]
