from __future__ import annotations

from heeg_auto.core.base_page import BasePage


class _Logger:
    def info(self, *args, **kwargs):
        return None


class _Page(BasePage):
    def __init__(self, texts: list[str]) -> None:
        super().__init__(driver=None, logger=_Logger(), root=None)
        self._texts = texts

    def iter_visible_texts(self):
        yield from self._texts


def test_assert_duration_in_range_matches_duration_token_in_visible_texts():
    page = _Page(
        texts=[
            "开始",
            "结束",
            "2026/04/09 10:44:36",
            "2026/04/09 10:44:39",
            "00:00:03",
        ]
    )

    page.assert_duration_in_range("00:00:02", "00:00:04", timeout=1)


def test_assert_control_enabled_accepts_enabled_control():
    page = _Page(texts=[])

    class _Control:
        def is_enabled(self):
            return True

    page.find = lambda locator, timeout=1: _Control()  # type: ignore[method-assign]

    page.assert_control_enabled({"title": "剪辑", "control_type": "Button"}, timeout=1)
