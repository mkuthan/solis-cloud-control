import base64
import hashlib
import hmac
from datetime import UTC, datetime


def digest(body: str) -> str:
    return base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")


def current_date() -> str:
    return datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")


def sign_authorization(key: str, message: str) -> str:
    hmac_object = hmac.new(
        key.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha1,
    )
    return base64.b64encode(hmac_object.digest()).decode("utf-8")
