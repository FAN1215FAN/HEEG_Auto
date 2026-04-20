from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowRect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def contains_point(rect: WindowRect, x: int, y: int) -> bool:
    return rect.left <= x <= rect.right and rect.top <= y <= rect.bottom


def point_to_ratio(rect: WindowRect, x: int, y: int) -> tuple[float, float]:
    if rect.width <= 0 or rect.height <= 0:
        raise ValueError(f"Invalid window rect: {rect}")
    x_ratio = (x - rect.left) / rect.width
    y_ratio = (y - rect.top) / rect.height
    return _clamp_ratio(x_ratio), _clamp_ratio(y_ratio)


def _clamp_ratio(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value
