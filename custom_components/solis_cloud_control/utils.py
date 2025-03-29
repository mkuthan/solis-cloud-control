import base64
import hashlib
import hmac
from datetime import UTC, datetime


def digest(body: str) -> str:
    return base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")


def current_date() -> datetime:
    return datetime.now(UTC)


def format_date(date: datetime) -> str:
    return date.strftime("%a, %d %b %Y %H:%M:%S GMT")


def sign_authorization(key: str, message: str) -> str:
    hmac_object = hmac.new(
        key.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha1,
    )
    return base64.b64encode(hmac_object.digest()).decode("utf-8")


def validate_time_range(value: str) -> bool:
    if len(value) != 11 or value.count("-") != 1:
        return False

    try:
        from_str, to_str = value.split("-")
        from_time = datetime.strptime(from_str, "%H:%M")
        to_time = datetime.strptime(to_str, "%H:%M")
        return to_time >= from_time
    except ValueError:
        return False
