from __future__ import annotations

import argparse
import ctypes
import msvcrt
import time
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime

from heeg_auto.assets import AssetStore
from heeg_auto.config.settings import INSPECTOR_DIR, ensure_artifact_dirs
from heeg_auto.core.window_ratio import WindowRect, contains_point, point_to_ratio

VK_LBUTTON = 0x01
POLL_INTERVAL_SECONDS = 0.05

_MODE_PREFIX_MAP = {
    "window": "窗口",
    "waveform": "波形",
    "timeline": "进度条",
}
_MODE_CALIBRATION_PREFIX_MAP = {
    "window": None,
    "waveform": "waveform",
    "timeline": "timeline",
}

user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


@dataclass(frozen=True)
class RatioSample:
    timestamp: str
    title: str
    hwnd: int
    x: int
    y: int
    window_rect: WindowRect
    ratio_rect: WindowRect
    window_x_ratio: float
    window_y_ratio: float
    scoped_x_ratio: float
    scoped_y_ratio: float
    mode: str


@dataclass(frozen=True)
class CaptureConfig:
    mode: str
    window_label: str
    ratio_prefix: str
    interaction_calibration: dict[str, float]


def pick_top_window_ratio(mode: str = "window", window_label: str = "") -> str:
    ensure_artifact_dirs()
    config = _build_capture_config(mode=mode, window_label=window_label)
    output_path = INSPECTOR_DIR / f"top_window_ratio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    print("比例读取工具已启动。")
    print(f"当前模式: {config.mode} | 比例前缀: {config.ratio_prefix}")
    if config.window_label:
        print(f"使用窗口资产: {config.window_label}")
    print("保持目标窗口在最上层，鼠标左键点击窗口内任意位置可输出比例。")
    print("连续点击两次会额外输出起点/终点 YAML 片段。")
    print("按 q 或 Esc 退出。")
    print(f"结果会同时写入: {output_path}")

    previous_down = False
    pending_sample: RatioSample | None = None
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key.lower() == "q" or key == "\x1b":
                break

        is_down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        if is_down and not previous_down:
            line, sample = _build_click_record(config)
            print(line)
            _append_log_line(output_path, line)
            if sample is not None:
                if pending_sample is None or pending_sample.hwnd != sample.hwnd:
                    pending_sample = sample
                else:
                    snippet = _build_pair_snippet(pending_sample, sample)
                    print(snippet)
                    _append_log_line(output_path, snippet)
                    pending_sample = None
        previous_down = is_down
        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"比例读取结束，结果文件: {output_path}")
    return str(output_path)


def _append_log_line(path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def _build_capture_config(mode: str, window_label: str) -> CaptureConfig:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in _MODE_PREFIX_MAP:
        raise ValueError(f"Unsupported mode: {mode}")

    interaction_calibration: dict[str, float] = {}
    normalized_label = window_label.strip()
    if normalized_mode != "window":
        if not normalized_label:
            raise ValueError("waveform/timeline 模式必须提供 --window-label。")
        window_asset = AssetStore().resolve_window(normalized_label)
        interaction_calibration = dict(window_asset.get("interaction_calibration") or {})

    return CaptureConfig(
        mode=normalized_mode,
        window_label=normalized_label,
        ratio_prefix=_MODE_PREFIX_MAP[normalized_mode],
        interaction_calibration=interaction_calibration,
    )


def _build_click_record(config: CaptureConfig) -> tuple[str, RatioSample | None]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return f"{timestamp} | 未获取到当前最上层窗口。", None

    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return f"{timestamp} | 未获取到当前鼠标坐标。", None

    rect_struct = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect_struct)):
        return f"{timestamp} | 未获取到窗口矩形 | hwnd={hwnd}", None

    window_rect = WindowRect(
        left=int(rect_struct.left),
        top=int(rect_struct.top),
        right=int(rect_struct.right),
        bottom=int(rect_struct.bottom),
    )
    ratio_rect = _resolve_ratio_rect(
        window_rect=window_rect,
        calibration=config.interaction_calibration,
        mode=config.mode,
    )
    title = _get_window_text(hwnd)
    x = int(point.x)
    y = int(point.y)
    if not contains_point(ratio_rect, x, y):
        return (
            f"{timestamp} | 标题: {title} | hwnd={hwnd} | 点击坐标=({x}, {y}) "
            f"| 取点区域=({ratio_rect.left}, {ratio_rect.top}, {ratio_rect.right}, {ratio_rect.bottom}) "
            f"| 点击不在当前取点区域内",
            None,
        )

    window_x_ratio, window_y_ratio = point_to_ratio(window_rect, x, y)
    scoped_x_ratio, scoped_y_ratio = point_to_ratio(ratio_rect, x, y)
    sample = RatioSample(
        timestamp=timestamp,
        title=title,
        hwnd=int(hwnd),
        x=x,
        y=y,
        window_rect=window_rect,
        ratio_rect=ratio_rect,
        window_x_ratio=window_x_ratio,
        window_y_ratio=window_y_ratio,
        scoped_x_ratio=scoped_x_ratio,
        scoped_y_ratio=scoped_y_ratio,
        mode=config.mode,
    )
    line = (
        f"{timestamp} | 标题: {title} | hwnd={hwnd} | 点击坐标=({x}, {y}) "
        f"| 窗口矩形=({window_rect.left}, {window_rect.top}, {window_rect.right}, {window_rect.bottom}) "
        f"| 取点区域=({ratio_rect.left}, {ratio_rect.top}, {ratio_rect.right}, {ratio_rect.bottom}) "
        f"| window_x_ratio={window_x_ratio:.4f} | window_y_ratio={window_y_ratio:.4f} "
        f"| {config.ratio_prefix}x比例={scoped_x_ratio:.4f} | {config.ratio_prefix}y比例={scoped_y_ratio:.4f}"
    )
    return line, sample


def _resolve_ratio_rect(window_rect: WindowRect, calibration: dict[str, float], mode: str) -> WindowRect:
    prefix = _MODE_CALIBRATION_PREFIX_MAP[mode]
    if prefix is None:
        return window_rect
    return _calibrated_rect(window_rect, calibration, prefix=prefix)


def _calibrated_rect(window_rect: WindowRect, calibration: dict[str, float], prefix: str) -> WindowRect:
    left_ratio = _require_ratio(calibration, f"{prefix}_left_ratio")
    right_ratio = _require_ratio(calibration, f"{prefix}_right_ratio")
    top_ratio = _require_ratio(calibration, f"{prefix}_top_ratio")
    bottom_ratio = _require_ratio(calibration, f"{prefix}_bottom_ratio")
    if right_ratio <= left_ratio:
        raise ValueError(f"{prefix} right_ratio must be > left_ratio")
    if bottom_ratio <= top_ratio:
        raise ValueError(f"{prefix} bottom_ratio must be > top_ratio")
    width = window_rect.width
    height = window_rect.height
    return WindowRect(
        left=int(round(window_rect.left + width * left_ratio)),
        top=int(round(window_rect.top + height * top_ratio)),
        right=int(round(window_rect.left + width * right_ratio)),
        bottom=int(round(window_rect.top + height * bottom_ratio)),
    )


def _require_ratio(calibration: dict[str, float], key: str) -> float:
    if key not in calibration:
        raise ValueError(f"Missing interaction calibration: {key}")
    return float(calibration[key])


def _build_pair_snippet(first: RatioSample, second: RatioSample) -> str:
    prefix = _MODE_PREFIX_MAP[first.mode]
    return "\n".join(
        [
            f"# {first.timestamp} ~ {second.timestamp} | {first.title}",
            f"{prefix}起点X比例: {first.scoped_x_ratio:.4f}",
            f"{prefix}起点Y比例: {first.scoped_y_ratio:.4f}",
            f"{prefix}终点X比例: {second.scoped_x_ratio:.4f}",
            f"{prefix}终点Y比例: {second.scoped_y_ratio:.4f}",
        ]
    )


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value or "<无标题窗口>"


def main() -> None:
    parser = argparse.ArgumentParser(description="Read x/y ratios from the current foreground window.")
    parser.add_argument(
        "--mode",
        choices=["window", "waveform", "timeline"],
        default="window",
        help="window: relative to the whole window; waveform/timeline: relative to calibrated region.",
    )
    parser.add_argument(
        "--window-label",
        default="",
        help="Formal window asset label. Required for waveform/timeline mode.",
    )
    args = parser.parse_args()
    pick_top_window_ratio(mode=args.mode, window_label=args.window_label)


if __name__ == "__main__":
    main()
