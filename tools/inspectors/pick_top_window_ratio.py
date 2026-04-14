from __future__ import annotations

import ctypes
import msvcrt
import time
from ctypes import wintypes
from datetime import datetime

from heeg_auto.config.settings import INSPECTOR_DIR, ensure_artifact_dirs
from heeg_auto.core.window_ratio import WindowRect, contains_point, point_to_ratio

VK_LBUTTON = 0x01
POLL_INTERVAL_SECONDS = 0.05

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


def pick_top_window_ratio() -> str:
    ensure_artifact_dirs()
    output_path = INSPECTOR_DIR / f"top_window_ratio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print("比例读取工具已启动。")
    print("保持目标软件在最上层，鼠标左键点击窗口内任意位置可输出比例。")
    print("按 q 或 Esc 退出。")
    print(f"结果会同时写入: {output_path}")

    previous_down = False
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key.lower() == "q" or key == "\x1b":
                break

        is_down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        if is_down and not previous_down:
            line = _build_click_record()
            print(line)
            with output_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        previous_down = is_down
        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"比例读取结束，结果文件: {output_path}")
    return str(output_path)


def _build_click_record() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return f"{timestamp} | 未获取到当前最上层窗口。"

    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return f"{timestamp} | 未获取到当前鼠标坐标。"

    rect_struct = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect_struct)):
        return f"{timestamp} | 未获取到窗口矩形 | hwnd={hwnd}"

    rect = WindowRect(
        left=int(rect_struct.left),
        top=int(rect_struct.top),
        right=int(rect_struct.right),
        bottom=int(rect_struct.bottom),
    )
    title = _get_window_text(hwnd)
    x = int(point.x)
    y = int(point.y)
    if not contains_point(rect, x, y):
        return (
            f"{timestamp} | 标题: {title} | hwnd={hwnd} | 点击坐标=({x}, {y}) "
            f"| 窗口矩形=({rect.left}, {rect.top}, {rect.right}, {rect.bottom}) | 点击不在窗口内"
        )

    x_ratio, y_ratio = point_to_ratio(rect, x, y)
    return (
        f"{timestamp} | 标题: {title} | hwnd={hwnd} | 点击坐标=({x}, {y}) "
        f"| 窗口矩形=({rect.left}, {rect.top}, {rect.right}, {rect.bottom}) "
        f"| x比例={x_ratio:.4f} | y比例={y_ratio:.4f}"
    )


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value or "<无标题窗口>"


def main() -> None:
    pick_top_window_ratio()


if __name__ == "__main__":
    main()
