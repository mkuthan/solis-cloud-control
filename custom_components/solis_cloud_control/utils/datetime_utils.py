from datetime import datetime

from homeassistant.util.dt import as_local

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_inverter_time(value: str | None) -> datetime | None:
    if value is None:
        return None

    try:
        dt = datetime.strptime(value, _TIME_FORMAT)
        return as_local(dt)
    except ValueError:
        return None


def format_inverter_time(dt: datetime) -> str:
    dt_local = as_local(dt)
    return dt_local.strftime(_TIME_FORMAT)
