from __future__ import annotations

DEFAULT_DURATION_TOLERANCE_SECONDS = 1.0


def parse_duration_seconds(raw_value, field_name: str) -> float:
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


def format_duration(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"


def normalize_tolerance_seconds(raw_value=None) -> float:
    if raw_value in (None, ""):
        return DEFAULT_DURATION_TOLERANCE_SECONDS
    return parse_duration_seconds(raw_value, field_name="duration_tolerance")


def derive_duration_range(
    start_time,
    end_time,
    *,
    tolerance_seconds=None,
) -> tuple[str, str]:
    start_seconds = parse_duration_seconds(start_time, field_name="start_time")
    end_seconds = parse_duration_seconds(end_time, field_name="end_time")
    if end_seconds < start_seconds:
        raise ValueError(f"结束时间必须大于等于开始时间: {start_time} ~ {end_time}")
    tolerance = normalize_tolerance_seconds(tolerance_seconds)
    duration_seconds = end_seconds - start_seconds
    min_seconds = max(0.0, duration_seconds - tolerance)
    max_seconds = duration_seconds + tolerance
    return format_duration(min_seconds), format_duration(max_seconds)
