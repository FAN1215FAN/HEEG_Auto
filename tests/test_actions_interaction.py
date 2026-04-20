from __future__ import annotations

from heeg_auto.config.settings import DEFAULT_TIMEOUT
from heeg_auto.core.base_page import BasePage
from heeg_auto.core.actions import ActionExecutor


class _Rect:
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class _Wrapper:
    def __init__(self, title: str, rect: tuple[int, int, int, int]) -> None:
        self.element_info = type("Info", (), {"name": title, "control_type": "Window"})()
        self._rect = _Rect(*rect)

    def rectangle(self):
        return self._rect

    def window_text(self):
        return self.element_info.name


class _Driver:
    def __init__(self) -> None:
        self.main_window_wrapper = _Wrapper("数字脑电采集记录软件", (0, 0, 1000, 500))
        self.main_window = self.main_window_wrapper
        self.desktop = type("Desktop", (), {"top_window": lambda self: None})()
        self.app = None

    def top_window(self):
        return None


class _Logger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None


def test_action_executor_scopes_target_lookup_to_explicit_window(monkeypatch):
    executor = ActionExecutor(driver=_Driver(), logger=_Logger())
    history_wrapper = _Wrapper("历史回放", (100, 50, 900, 450))
    executor.main_page.find = lambda locator, timeout=30: history_wrapper
    captured = {}

    original_click = BasePage.click

    def fake_click(self, locator):
        captured["root"] = getattr(self, "root", None)
        captured["locator"] = locator

    monkeypatch.setattr(BasePage, "click", fake_click)
    try:
        executor.click(
            target={"title": "数据剪辑", "control_type": "Button", "class_name": "Button"},
            window={"title": "历史回放", "control_type": "Window", "class_name": "Window"},
        )
    finally:
        monkeypatch.setattr(BasePage, "click", original_click)

    assert captured["root"] is history_wrapper
    assert captured["locator"]["title"] == "数据剪辑"


def test_action_executor_clicks_timeline_time_on_history_replay_window():
    executor = ActionExecutor(driver=_Driver(), logger=_Logger())
    history_wrapper = _Wrapper("历史回放", (100, 50, 900, 450))
    executor.main_page.find = lambda locator, timeout=30: history_wrapper
    captured = {}
    executor.main_page.click_point = lambda x, y, button="left", double=False: captured.update({"x": x, "y": y})

    executor.click(
        window={
            "title": "历史回放",
            "interaction_calibration": {
                "timeline_left_ratio": 0.10,
                "timeline_right_ratio": 0.90,
                "timeline_top_ratio": 0.80,
                "timeline_bottom_ratio": 0.90,
            },
        },
        **{"定位方式": "进度条时间", "目标时间": "00:00:30", "总时长": "00:01:00"},
    )

    assert captured == {"x": 500, "y": 390}


def test_action_executor_drags_waveform_by_ratio():
    executor = ActionExecutor(driver=_Driver(), logger=_Logger())
    captured = {}
    executor.main_page.drag_point = lambda sx, sy, ex, ey, button="left": captured.update(
        {"start": (sx, sy), "end": (ex, ey)}
    )

    executor.drag(
        window={
            "title": "数字脑电采集记录软件",
            "interaction_calibration": {
                "waveform_left_ratio": 0.20,
                "waveform_right_ratio": 0.80,
                "waveform_top_ratio": 0.10,
                "waveform_bottom_ratio": 0.70,
            },
        },
        **{"定位方式": "波形比例", "起点X比例": 0.25, "起点Y比例": 0.50, "终点X比例": 0.75, "终点Y比例": 0.50},
    )

    assert captured["start"] == (350, 200)
    assert captured["end"] == (650, 200)


def test_action_executor_asserts_latest_clipped_record():
    executor = ActionExecutor(driver=_Driver(), logger=_Logger())
    captured = {}
    executor.main_page.assert_latest_clipped_record = lambda **kwargs: captured.update(kwargs)

    executor.assert_latest_clipped_record(
        **{"记录名称": "自动化测试数据1", "开始时间": "00:00:01", "结束时间": "00:00:04", "原始时长": "00:00:42"}
    )

    assert captured == {
        "record_name": "自动化测试数据1",
        "expected_duration": None,
        "min_duration": "00:00:02",
        "max_duration": "00:00:04",
        "original_duration": "00:00:42",
        "timeout": DEFAULT_TIMEOUT,
    }


def test_action_executor_asserts_duration_range_from_start_and_end():
    executor = ActionExecutor(driver=_Driver(), logger=_Logger())
    captured = {}
    executor.main_page.assert_duration_in_range = lambda **kwargs: captured.update(kwargs)

    executor.assert_duration_in_range(**{"开始时间": "00:00:01", "结束时间": "00:00:04"})

    assert captured == {
        "min_duration": "00:00:02",
        "max_duration": "00:00:04",
        "timeout": DEFAULT_TIMEOUT,
    }
