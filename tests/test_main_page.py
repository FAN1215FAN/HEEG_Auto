from __future__ import annotations

from heeg_auto.pages.main_page import MainPage


class _Rect:
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class _Wrapper:
    def __init__(
        self,
        *,
        text: str = "",
        control_type: str = "Text",
        rect: tuple[int, int, int, int] = (0, 0, 10, 10),
        children: list["_Wrapper"] | None = None,
    ) -> None:
        self._text = text
        self.element_info = type("Info", (), {"name": text, "control_type": control_type})()
        self._rect = _Rect(*rect)
        self._children = children or []

    def is_visible(self):
        return True

    def window_text(self):
        return self._text

    def rectangle(self):
        return self._rect

    def descendants(self):
        result = []
        for child in self._children:
            result.append(child)
            result.extend(child.descendants())
        return result


class _Driver:
    def __init__(self, main_window_wrapper) -> None:
        self.main_window_wrapper = main_window_wrapper


class _Logger:
    def info(self, *args, **kwargs):
        return None


def test_main_page_asserts_latest_clipped_record_when_row_texts_are_split_across_cells():
    root = _Wrapper(
        control_type="Window",
        children=[
            _Wrapper(text="设备名称", rect=(20, 100, 120, 120)),
            _Wrapper(text="持续时间", rect=(200, 100, 300, 120)),
            _Wrapper(text="自动化测试数据1", rect=(20, 200, 160, 222)),
            _Wrapper(text="00:00:42", rect=(220, 202, 300, 222)),
            _Wrapper(text="自动化测试数据1", rect=(20, 236, 160, 258)),
            _Wrapper(text="00:00:02", rect=(220, 238, 300, 258)),
            _Wrapper(text="<0.01", rect=(340, 236, 390, 258)),
        ],
    )
    page = MainPage(driver=_Driver(root), logger=_Logger())

    page.assert_latest_clipped_record(
        record_name="自动化测试数据1",
        expected_duration="00:00:02",
        original_duration="00:00:42",
        timeout=1,
    )
