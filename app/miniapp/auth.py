"""Verify signed Telegram Mini App initData, never user-supplied identities."""

import hashlib
import hmac
import json
import re
import time
from urllib.parse import parse_qsl


class InvalidMiniAppAuth(ValueError):
    pass


def verify_init_data(raw: str, token: str, *, now: int | None = None) -> int:
    """Return the signed Telegram user ID; reject stale, ambiguous or unsigned data."""
    try:
        if (
            type(raw) is not str
            or not 1 <= len(raw.encode("utf-8")) <= 8192
            or not token
        ):
            raise ValueError
        pairs = parse_qsl(
            raw, keep_blank_values=True, strict_parsing=True,
            encoding="utf-8", errors="strict", max_num_fields=32,
        )
        values = dict(pairs)
        if len(values) != len(pairs):
            raise ValueError
        signature = values.get("hash", "")
        stamp = values.get("auth_date", "")
        if (
            not re.fullmatch(r"[0-9a-fA-F]{64}", signature)
            or not stamp.isascii()
            or not stamp.isdecimal()
            or len(stamp) > 12
        ):
            raise ValueError
        issued = int(stamp)
        current = int(time.time()) if now is None else now
        if issued > current + 30 or current - issued > 3600:
            raise ValueError
        check_string = "\n".join(
            sorted(f"{key}={value}" for key, value in pairs if key != "hash")
        )
        secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature.lower(), expected):
            raise ValueError
        if values.get("chat_type") not in (None, "private"):
            raise ValueError
        identity = json.loads(values["user"])
        if type(identity) is not dict:
            raise ValueError
        user_id = identity.get("id")
        if type(user_id) is not int or not 1 <= user_id < 2**63:
            raise ValueError
        return user_id
    except (ValueError, KeyError, UnicodeError, TypeError, json.JSONDecodeError):
        raise InvalidMiniAppAuth("invalid Mini App authentication") from None
