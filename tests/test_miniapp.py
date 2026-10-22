"""Mini App authentication and read-only entry-point checks."""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
import pytest

from app.api.main import app
from app.miniapp.auth import InvalidMiniAppAuth, verify_init_data

TOKEN = "12345:test-bot-token"


def signed(user_id=55, issued=1700000000, extra=None):
    values = {
        "auth_date": str(issued),
        "user": json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":")),
        **(extra or {}),
    }
    body = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(key, body.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


def test_signed_user_fresh_and_no_client_identity_override():
    assert verify_init_data(signed(), TOKEN, now=1700000001) == 55
    assert verify_init_data(signed(999), TOKEN, now=1700000001) == 999


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "user=%7B%22id%22%3A55%7D&auth_date=1700000000",
        signed().replace("55", "56"),
        signed() + "&user=%7B%7D",
        signed() + "&hash=" + "0" * 64,
        signed(issued=1699996000),
        signed(issued=1700000040),
        signed(user_id=True),
        signed(extra={"chat_type": "group"}),
    ],
)
def test_reject_invalid_forged_expired_or_ambiguous(raw):
    with pytest.raises(InvalidMiniAppAuth):
        verify_init_data(raw, TOKEN, now=1700000000)


def test_missing_server_token_is_not_auth():
    with pytest.raises(InvalidMiniAppAuth):
        verify_init_data(signed(), "", now=1700000001)


@pytest.mark.parametrize("path", ["/miniapp", "/miniapp/app.js", "/miniapp/styles.css"])
async def test_ui_assets_are_available_without_silent_checkout(path):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(path)
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert "Content-Security-Policy" in resp.headers if path == "/miniapp" else True


async def test_no_init_data_no_session_and_no_order_creation():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/miniapp/api/overview", json={"init_data": "auth_date=1700000000"}
        )
    assert resp.status_code == 401
    assert resp.headers["cache-control"] == "no-store"
    assert "user" not in resp.text.lower()


def test_auth_window_uses_received_timestamp():
    now = int(datetime.now(UTC).timestamp())
    assert verify_init_data(signed(issued=now - 3500), TOKEN, now=now) == 55
    with pytest.raises(InvalidMiniAppAuth):
        verify_init_data(signed(issued=now - 3601), TOKEN, now=now)
