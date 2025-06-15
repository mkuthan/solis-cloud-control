from datetime import datetime


def validate_time_range(value: str) -> bool:
    if len(value) != len("HH:MM-HH:MM") or value.count("-") != 1:
        return False

    try:
        from_str, to_str = value.split("-")
        from_time = datetime.strptime(from_str, "%H:%M")
        to_time = datetime.strptime(to_str, "%H:%M")
        return to_time >= from_time
    except ValueError:
        return False
