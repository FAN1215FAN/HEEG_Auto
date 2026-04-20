from __future__ import annotations

from heeg_auto.core.duration_utils import derive_duration_range, format_duration, parse_duration_seconds


def test_parse_duration_seconds_supports_hh_mm_ss():
    assert parse_duration_seconds("00:01:05", field_name="duration") == 65


def test_format_duration_rounds_to_hh_mm_ss():
    assert format_duration(3.4) == "00:00:03"


def test_derive_duration_range_uses_default_one_second_tolerance():
    assert derive_duration_range("00:00:01", "00:00:04") == ("00:00:02", "00:00:04")
