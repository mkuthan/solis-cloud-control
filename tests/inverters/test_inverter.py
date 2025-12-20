from dataclasses import replace

import pytest

from custom_components.solis_cloud_control.inverters.inverter import InverterInfo, InverterOnOff


@pytest.mark.parametrize(
    "energy_storage_control,expected",
    [
        ("0", True),
        ("1", False),
        (None, False),
        ("", False),
        ("unexpected", False),
    ],
)
def test_inverter_info_is_string_inverter(any_inverter_info, energy_storage_control, expected):
    inverter = replace(any_inverter_info, energy_storage_control=energy_storage_control)
    assert inverter.is_string_inverter == expected


@pytest.mark.parametrize(
    "tou_v2_mode,expected",
    [
        (InverterInfo.TOU_V2_MODE, True),
        (None, False),
        ("", False),
        ("unexpected", False),
    ],
)
def test_inverter_info_is_tou_v2_enabled(any_inverter_info, tou_v2_mode, expected):
    inverter = replace(any_inverter_info, tou_v2_mode=tou_v2_mode)
    assert inverter.is_tou_v2_enabled == expected


@pytest.mark.parametrize(
    "power, power_unit, parallel_inverter_count, expected_power",
    [
        ("5", "kW", "1", 5000.0),
        ("5", "kW", "2", 10000.0),
        ("5000", "W", "1", 5000.0),
        ("5000", "W", "2", 10000.0),
        ("5.5", "kW", "1", 5500.0),
        ("5.5", "kW", "2", 11000.0),
        ("5500.5", "W", "1", 5500.5),
        ("5500.5", "W", "2", 11001.0),
        ("invalid", "kW", "1", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
        ("5", "invalid", "1", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
        ("5", None, "1", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
        (None, "kW", "1", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
        (None, None, "1", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
        (None, None, "2", InverterInfo.MAX_EXPORT_POWER_DEFAULT),
    ],
)
def test_inverter_max_export_power(any_inverter_info, power, power_unit, parallel_inverter_count, expected_power):
    inverter = replace(any_inverter_info, power=power, power_unit=power_unit, parallel_number=parallel_inverter_count)

    assert inverter.max_export_power == expected_power


@pytest.mark.parametrize(
    "model,expected_scale",
    [
        ("3173", 0.01),
        ("3315", 0.01),
        ("3331", 0.01),
        ("any_model", 1.0),
    ],
)
def test_inverter_info_max_export_power_scale(any_inverter_info, model, expected_scale):
    inverter = replace(any_inverter_info, model=model)
    assert inverter.max_export_power_scale == expected_scale


@pytest.mark.parametrize(
    "parallel_number,expected",
    [
        ("1", 1),
        ("2", 2),
        ("1.0", 1),
        ("2.0", 2),
        ("", 1),
        ("invalid", 1),
        ("-1.5", 1),
        ("-1", 1),
        ("-0.5", 1),
        ("0", 1),
        ("0.0", 1),
        ("0.5", 1),
        ("1.5", 1),
        (None, 1),
    ],
)
def test_inverter_info_parallel_inverter_count(any_inverter_info, parallel_number, expected):
    inverter = replace(any_inverter_info, parallel_number=parallel_number)
    assert inverter.parallel_inverter_count == expected


@pytest.mark.parametrize(
    "parallel_battery,expected",
    [
        ("0", 1),
        ("0.0", 1),
        ("1", 2),
        ("1.0", 2),
        ("", 1),
        ("invalid", 1),
        ("-1.5", 1),
        ("-1", 1),
        ("-0.5", 1),
        ("0.5", 1),
        ("1.5", 1),
        (None, 1),
    ],
)
def test_inverter_info_parallel_battery_count(any_inverter_info, parallel_battery, expected):
    inverter = replace(any_inverter_info, parallel_battery=parallel_battery)
    assert inverter.parallel_battery_count == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("190", True),
        ("222", True),
        ("0", False),
        ("", False),
        ("invalid", False),
        (None, False),
    ],
)
def test_inverter_on_off_is_valid_value(value, expected):
    inverter_on_off = InverterOnOff()
    assert inverter_on_off.is_valid_value(value) == expected
