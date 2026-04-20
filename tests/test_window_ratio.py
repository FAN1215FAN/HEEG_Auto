from __future__ import annotations

import pytest

from heeg_auto.core.window_ratio import WindowRect, contains_point, point_to_ratio


def test_point_to_ratio_returns_expected_relative_position():
    rect = WindowRect(left=100, top=200, right=500, bottom=1000)

    x_ratio, y_ratio = point_to_ratio(rect, 200, 600)

    assert x_ratio == 0.25
    assert y_ratio == 0.5


def test_contains_point_checks_window_bounds():
    rect = WindowRect(left=10, top=20, right=110, bottom=220)

    assert contains_point(rect, 10, 20) is True
    assert contains_point(rect, 110, 220) is True
    assert contains_point(rect, 9, 20) is False


def test_point_to_ratio_rejects_invalid_rect():
    rect = WindowRect(left=30, top=30, right=30, bottom=60)

    with pytest.raises(ValueError, match="Invalid window rect"):
        point_to_ratio(rect, 30, 40)
