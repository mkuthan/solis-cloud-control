def safe_get_float_value(value_str: str | None) -> float | None:
    if value_str is None:
        return None
    try:
        return float(value_str)
    except ValueError:
        return None


def safe_get_int_value(value_str: str | None) -> int | None:
    if value_str is None:
        return None
    try:
        return int(value_str)
    except ValueError:
        return None


def safe_convert_power_to_watts(power: str | float | None, power_unit: str | None) -> float | None:
    if power is None or power_unit is None:
        return None

    try:
        power_float = float(power)
    except (ValueError, TypeError):
        return None

    if power_unit == "kW":
        return power_float * 1000
    if power_unit == "W":
        return power_float

    return None
