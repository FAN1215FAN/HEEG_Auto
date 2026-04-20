from __future__ import annotations

from heeg_auto.core.window_ratio import WindowRect
from tools.inspectors.pick_top_window_ratio import RatioSample, _build_pair_snippet, _resolve_ratio_rect


def test_resolve_ratio_rect_uses_waveform_calibration():
    rect = WindowRect(left=100, top=50, right=900, bottom=450)
    ratio_rect = _resolve_ratio_rect(
        window_rect=rect,
        calibration={
            "waveform_left_ratio": 0.10,
            "waveform_right_ratio": 0.90,
            "waveform_top_ratio": 0.20,
            "waveform_bottom_ratio": 0.80,
        },
        mode="waveform",
    )

    assert ratio_rect == WindowRect(left=180, top=130, right=820, bottom=370)


def test_build_pair_snippet_outputs_yaml_ready_waveform_ratios():
    sample_a = RatioSample(
        timestamp="2026-04-20 12:00:00",
        title="历史回放",
        hwnd=1,
        x=100,
        y=200,
        window_rect=WindowRect(0, 0, 1000, 500),
        ratio_rect=WindowRect(100, 50, 900, 450),
        window_x_ratio=0.10,
        window_y_ratio=0.40,
        scoped_x_ratio=0.1250,
        scoped_y_ratio=0.3750,
        mode="waveform",
    )
    sample_b = RatioSample(
        timestamp="2026-04-20 12:00:02",
        title="历史回放",
        hwnd=1,
        x=300,
        y=220,
        window_rect=WindowRect(0, 0, 1000, 500),
        ratio_rect=WindowRect(100, 50, 900, 450),
        window_x_ratio=0.30,
        window_y_ratio=0.44,
        scoped_x_ratio=0.3750,
        scoped_y_ratio=0.4250,
        mode="waveform",
    )

    snippet = _build_pair_snippet(sample_a, sample_b)

    assert "波形起点X比例: 0.1250" in snippet
    assert "波形起点Y比例: 0.3750" in snippet
    assert "波形终点X比例: 0.3750" in snippet
    assert "波形终点Y比例: 0.4250" in snippet
