"""Short-lived, owner-bound proof that a specific complete draft was reviewed."""

import hashlib
import hmac
import re
import time

from app.core.settings import config


class InvalidReviewToken(ValueError):
    pass


def _signature(user_id, value):
    secret = hmac.new(
        config().bot_token.get_secret_value().encode(), b"MiniAppReview-v1", hashlib.sha256
    ).digest()
    return hmac.new(secret, f"{user_id}:{value}".encode(), hashlib.sha256).hexdigest()


def issue(user_id, key, revision, *, now=None):
    stamp = int(time.time()) if now is None else now
    value = f"{key}.{revision}.{stamp}"
    return value + "." + _signature(user_id, value)


def verify(user_id, token, *, now=None):
    match = re.fullmatch(r"([a-f0-9]{32})\.([a-f0-9]{64})\.([0-9]{1,12})\.([a-f0-9]{64})", token)
    if not match:
        raise InvalidReviewToken("invalid review")
    key, revision, issued, signature = match.groups()
    current = int(time.time()) if now is None else now
    if (
        int(issued) > current + 30
        or current - int(issued) > 3600
        or not hmac.compare_digest(signature, _signature(user_id, token.rsplit(".", 1)[0]))
    ):
        raise InvalidReviewToken("invalid review")
    return key, revision
