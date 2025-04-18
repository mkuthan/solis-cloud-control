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
