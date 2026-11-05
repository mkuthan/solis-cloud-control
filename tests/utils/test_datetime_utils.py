from datetime import datetime

import pytest

from custom_components.solis_cloud_control.utils.datetime_utils import format_inverter_time, parse_inverter_time


def test_parse_inverter_time():
    result = parse_inverter_time("2025-12-11 17:00:00")

    assert result is not None
    assert result.replace(tzinfo=None) == datetime(2025, 12, 11, 17, 0, 0)


@pytest.mark.parametrize("value", [None, "invalid", "2025-12-11T17:00:00"])
def test_parse_inverter_time_invalid(value):
    assert parse_inverter_time(value) is None


def test_format_inverter_time():
    assert format_inverter_time(datetime(2025, 12, 11, 17, 0, 0)) == "2025-12-11 17:00:00"
