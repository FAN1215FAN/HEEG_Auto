from __future__ import annotations

from datetime import datetime
from typing import Any

from heeg_auto.config.locators import resolve_locator
from heeg_auto.config.settings import DEFAULT_TIMEOUT
from heeg_auto.core.base_page import BasePage
from heeg_auto.pages.create_patient_dialog import CreatePatientDialogPage
from heeg_auto.pages.main_page import MainPage

ACTION_ALIASES = {
    "launch_app": "launch_app",
    "启动应用": "launch_app",
    "click": "click",
    "点击": "click",
    "单击": "click",
    "double_click": "double_click",
    "双击": "double_click",
    "right_click": "right_click",
    "右键": "right_click",
    "drag": "drag",
    "拖动": "drag",
    "input_text": "input_text",
    "输入": "input_text",
    "select_combo": "select_combo",
    "下拉选择": "select_combo",
    "select_radio": "select_radio",
    "选择单选": "select_radio",
    "set_checkbox": "set_checkbox",
    "设置复选框": "set_checkbox",
    "wait_for_window": "wait_for_window",
    "等待窗口": "wait_for_window",
    "wait_visible": "wait_visible",
    "等待可见": "wait_visible",
    "assert_exists": "assert_exists",
    "断言存在": "assert_exists",
    "assert_window_closed": "assert_window_closed",
    "断言窗口关闭": "assert_window_closed",
    "assert_text_visible": "assert_text_visible",
    "断言文本可见": "assert_text_visible",
    "assert_text_not_visible": "assert_text_not_visible",
    "断言文本不可见": "assert_text_not_visible",
    "assert_latest_clipped_record": "assert_latest_clipped_record",
    "断言最新剪辑记录": "assert_latest_clipped_record",
    "screenshot": "screenshot",
    "截图": "screenshot",
}

_REUSE_SESSION_VALUES = {"自动复用", "reuse"}
_POSITION_MODE_ALIASES = {
    "window_ratio": "window_ratio",
    "窗口比例": "window_ratio",
    "waveform_ratio": "waveform_ratio",
    "波形比例": "waveform_ratio",
    "timeline_time": "timeline_time",
    "进度条时间": "timeline_time",
}


class ActionExecutor:
    def __init__(self, driver, logger) -> None:
        self.driver = driver
        self.logger = logger
        self.main_page = MainPage(driver=driver, logger=logger)
        self.dialog_page = None

    def resolve_action_name(self, action_name: str) -> str:
        if action_name not in ACTION_ALIASES:
            raise KeyError(f"Unsupported action: {action_name}")
        return ACTION_ALIASES[action_name]

    def resolve_target(self, target, default_page: str | None = None) -> dict:
        locator = resolve_locator(target, default_page=default_page)
        self.logger.info("Resolved target %s -> %s", target, locator)
        return locator

    def ensure_session(self, exe_path: str | None = None, session_mode: str = "自动复用") -> str:
        if session_mode in _REUSE_SESSION_VALUES:
            mode = self.driver.reuse_existing(exe_path=exe_path)
        else:
            mode = self.driver.launch(exe_path=exe_path)
        self.main_page = MainPage(driver=self.driver, logger=self.logger)
        self.dialog_page = None
        return mode

    def launch_app(self, exe_path: str | None = None, session_mode: str = "自动复用", **_: dict) -> str:
        return self.ensure_session(exe_path=exe_path, session_mode=session_mode)

    def click(self, target=None, window=None, **kwargs: dict) -> None:
        if target not in (None, ""):
            locator = self.resolve_target(target)
            page = self._page_for_target(locator, window=window)
            page.click(locator)
            return
        point = self._build_click_point(window=window, params=kwargs)
        self.main_page.click_point(*point)

    def double_click(self, target, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.double_click(locator)

    def right_click(self, target, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.right_click(locator)

    def drag(self, target=None, window=None, **kwargs: dict) -> None:
        if target not in (None, ""):
            raise ValueError("当前拖动动作只支持基于窗口标定的坐标拖动，不支持直接传元素。")
        start_point, end_point = self._build_drag_points(window=window, params=kwargs)
        self.main_page.drag_point(*start_point, *end_point)

    def wait_for_window(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target, default_page="main")
        if locator.get("title") and self._is_main_window_locator(locator):
            self.main_page.assert_text_visible(locator["title"], timeout=timeout)
            return
        if locator.get("title") and locator.get("title") == "创建患者":
            self.dialog_page = CreatePatientDialogPage(driver=self.driver, logger=self.logger)
            self.dialog_page.wait_open(marker_text=locator["title"], timeout=timeout)
            return
        self.main_page.find(locator, timeout=timeout)

    def wait_visible(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator)
        page.find(locator, timeout=timeout)

    def assert_exists(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator)
        page.find(locator, timeout=timeout)

    def input_text(self, target, value: str, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.input_text(locator, value)

    def select_combo(self, target, value: str, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.select_combo(locator, value)

    def select_radio(self, target, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.select_radio(locator)

    def set_checkbox(self, target, value, window=None, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for_target(locator, window=window)
        page.set_checkbox(locator, value)

    def assert_window_closed(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target, default_page="main")
        if locator.get("title"):
            if self.dialog_page is not None and getattr(self.dialog_page, "root", None) is not None:
                self.dialog_page.wait_closed(timeout=timeout)
            else:
                self.main_page.assert_text_not_visible(locator["title"], timeout=timeout)
            self.dialog_page = None
            return
        self.main_page.wait_closed(locator, timeout=timeout)

    def assert_text_visible(
        self,
        text: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        window=None,
        **kwargs: dict,
    ) -> None:
        scoped_text = text or kwargs.get("文本")
        if not scoped_text:
            raise ValueError("断言文本可见必须提供 text/文本 参数。")
        if window in (None, ""):
            self.main_page.assert_text_visible(text=scoped_text, timeout=timeout)
            return
        window_locator = self.resolve_target(window, default_page="main")
        wrapper = self.main_page.find(window_locator, timeout=timeout)
        scoped_page = BasePage(driver=self.driver, logger=self.logger, root=wrapper)
        scoped_page.assert_text_visible(text=scoped_text, timeout=timeout)

    def assert_text_not_visible(
        self,
        text: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        window=None,
        **kwargs: dict,
    ) -> None:
        scoped_text = text or kwargs.get("文本")
        if not scoped_text:
            raise ValueError("断言文本不可见必须提供 text/文本 参数。")
        if window in (None, ""):
            self.main_page.assert_text_not_visible(text=scoped_text, timeout=timeout)
            return
        window_locator = self.resolve_target(window, default_page="main")
        wrapper = self.main_page.find(window_locator, timeout=timeout)
        scoped_page = BasePage(driver=self.driver, logger=self.logger, root=wrapper)
        scoped_page.assert_text_not_visible(text=scoped_text, timeout=timeout)

    def assert_latest_clipped_record(
        self,
        record_name: str | None = None,
        expected_duration: str | None = None,
        original_duration: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs: dict,
    ) -> None:
        record_name = record_name or kwargs.get("记录名称")
        expected_duration = expected_duration or kwargs.get("预期时长")
        original_duration = original_duration or kwargs.get("原始时长")
        if not record_name or not expected_duration:
            raise ValueError("断言最新剪辑记录必须提供 记录名称 和 预期时长。")
        self.main_page.assert_latest_clipped_record(
            record_name=record_name,
            expected_duration=expected_duration,
            original_duration=original_duration,
            timeout=timeout,
        )

    def screenshot(self, file_name: str | None = None, **_: dict) -> None:
        if not file_name:
            file_name = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.capture_screenshot(file_name)

    def _build_click_point(self, window, params: dict[str, Any]) -> tuple[int, int]:
        window_locator = self._resolve_window_locator(window)
        mode = self._resolve_position_mode(params)
        if mode == "timeline_time":
            bounds = self._resolve_bounds(window_locator, mode)
            total_seconds = self._parse_duration_seconds(
                params.get("总时长") or params.get("total_duration"),
                "总时长",
            )
            target_seconds = self._parse_duration_seconds(
                params.get("目标时间") or params.get("target_time"),
                "目标时间",
            )
            if total_seconds <= 0:
                raise ValueError("总时长必须大于 0。")
            if target_seconds < 0 or target_seconds > total_seconds:
                raise ValueError(f"目标时间超出总时长范围: {target_seconds} > {total_seconds}")
            x_ratio = target_seconds / total_seconds
            y_ratio = self._normalize_ratio(params.get("y比例", 0.5), "y比例")
            return self._ratio_to_point(bounds, x_ratio, y_ratio)

        bounds = self._resolve_bounds(window_locator, mode)
        x_ratio = self._normalize_ratio(params.get("x比例"), "x比例")
        y_ratio = self._normalize_ratio(params.get("y比例"), "y比例")
        return self._ratio_to_point(bounds, x_ratio, y_ratio)

    def _build_drag_points(self, window, params: dict[str, Any]) -> tuple[tuple[int, int], tuple[int, int]]:
        window_locator = self._resolve_window_locator(window)
        mode = self._resolve_position_mode(params)
        if mode not in {"waveform_ratio", "window_ratio"}:
            raise ValueError("当前拖动动作只支持波形比例或窗口比例。")
        bounds = self._resolve_bounds(window_locator, mode)
        start_x_ratio = self._normalize_ratio(params.get("起点X比例"), "起点X比例")
        start_y_ratio = self._normalize_ratio(params.get("起点Y比例"), "起点Y比例")
        end_x_ratio = self._normalize_ratio(params.get("终点X比例"), "终点X比例")
        end_y_ratio = self._normalize_ratio(params.get("终点Y比例"), "终点Y比例")
        return (
            self._ratio_to_point(bounds, start_x_ratio, start_y_ratio),
            self._ratio_to_point(bounds, end_x_ratio, end_y_ratio),
        )

    def _resolve_window_locator(self, window) -> dict[str, Any]:
        if window in (None, ""):
            raise ValueError("复杂交互步骤必须显式提供窗口。")
        return self.resolve_target(window, default_page="main")

    def _resolve_bounds(self, window_locator: dict[str, Any], mode: str) -> tuple[int, int, int, int]:
        wrapper = self._interaction_wrapper(window_locator)
        full_bounds = self.main_page.rectangle_from_wrapper(wrapper)
        if mode == "window_ratio":
            return full_bounds
        calibration = window_locator.get("interaction_calibration") or {}
        if mode == "waveform_ratio":
            return self._calibrated_bounds(full_bounds, calibration, prefix="waveform")
        if mode == "timeline_time":
            return self._calibrated_bounds(full_bounds, calibration, prefix="timeline")
        raise ValueError(f"不支持的定位方式: {mode}")

    def _interaction_wrapper(self, window_locator: dict[str, Any]):
        if self._is_main_window_locator(window_locator):
            return self.driver.main_window_wrapper
        return self.main_page.find(window_locator)

    @staticmethod
    def _calibrated_bounds(
        full_bounds: tuple[int, int, int, int],
        calibration: dict[str, Any],
        prefix: str,
    ) -> tuple[int, int, int, int]:
        left_ratio = ActionExecutor._normalize_ratio(calibration.get(f"{prefix}_left_ratio"), f"{prefix}_left_ratio")
        right_ratio = ActionExecutor._normalize_ratio(calibration.get(f"{prefix}_right_ratio"), f"{prefix}_right_ratio")
        top_ratio = ActionExecutor._normalize_ratio(calibration.get(f"{prefix}_top_ratio"), f"{prefix}_top_ratio")
        bottom_ratio = ActionExecutor._normalize_ratio(calibration.get(f"{prefix}_bottom_ratio"), f"{prefix}_bottom_ratio")
        if right_ratio <= left_ratio:
            raise ValueError(f"{prefix} 的左右比例配置不正确。")
        if bottom_ratio <= top_ratio:
            raise ValueError(f"{prefix} 的上下比例配置不正确。")
        left, top, right, bottom = full_bounds
        width = right - left
        height = bottom - top
        return (
            int(round(left + width * left_ratio)),
            int(round(top + height * top_ratio)),
            int(round(left + width * right_ratio)),
            int(round(top + height * bottom_ratio)),
        )

    @staticmethod
    def _ratio_to_point(bounds: tuple[int, int, int, int], x_ratio: float, y_ratio: float) -> tuple[int, int]:
        left, top, right, bottom = bounds
        width = right - left
        height = bottom - top
        x = int(round(left + width * x_ratio))
        y = int(round(top + height * y_ratio))
        return x, y

    @staticmethod
    def _resolve_position_mode(params: dict[str, Any]) -> str:
        raw_mode = params.get("定位方式") or params.get("position_mode")
        if raw_mode in (None, ""):
            raise ValueError("复杂交互步骤必须提供定位方式。")
        mode = _POSITION_MODE_ALIASES.get(str(raw_mode).strip())
        if mode is None:
            raise KeyError(f"未注册的定位方式: {raw_mode}")
        return mode

    @staticmethod
    def _normalize_ratio(raw_value: Any, field_name: str) -> float:
        if raw_value in (None, ""):
            raise ValueError(f"缺少必要参数: {field_name}")
        try:
            ratio = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"比例参数非法: {field_name}={raw_value}") from exc
        if ratio < 0 or ratio > 1:
            raise ValueError(f"比例参数必须在 0~1 之间: {field_name}={ratio}")
        return ratio

    @staticmethod
    def _parse_duration_seconds(raw_value: Any, field_name: str) -> float:
        if raw_value in (None, ""):
            raise ValueError(f"缺少必要参数: {field_name}")
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        text = str(raw_value).strip()
        if not text:
            raise ValueError(f"缺少必要参数: {field_name}")
        parts = text.split(":")
        try:
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + float(seconds)
            return float(text)
        except ValueError as exc:
            raise ValueError(f"时间参数格式非法: {field_name}={raw_value}") from exc

    def _page_for(self, locator: dict):
        page_name = locator.get("page")
        if page_name == "dialog":
            if self.dialog_page is None:
                self.dialog_page = CreatePatientDialogPage(driver=self.driver, logger=self.logger)
                self.dialog_page.wait_open()
            return self.dialog_page
        return self.main_page

    def _page_for_target(self, locator: dict, window=None):
        page = self._page_for(locator)
        if window in (None, "") or page is not self.main_page:
            return page
        window_locator = self.resolve_target(window, default_page="main")
        if self._is_main_window_locator(window_locator):
            return self.main_page
        try:
            wrapper = self.main_page.find(window_locator)
        except Exception:
            return self.main_page
        return BasePage(driver=self.driver, logger=self.logger, root=wrapper)

    def _is_main_window_locator(self, locator: dict) -> bool:
        title = locator.get("title", "")
        if not title:
            return False
        main_window = getattr(self.driver, "main_window_wrapper", None)
        if main_window is None:
            return False
        for getter in (
            lambda: main_window.window_text(),
            lambda: getattr(main_window.element_info, "name", ""),
        ):
            try:
                candidate = getter()
            except Exception:
                candidate = ""
            if candidate == title:
                return True
        return False
