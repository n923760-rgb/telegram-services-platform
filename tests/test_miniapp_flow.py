"""Database-backed Mini App privacy, activation and payment-view tests."""

from datetime import UTC, datetime

import httpx
from pydantic import SecretStr
from sqlalchemy import func, select

from app.api.main import app
from app.core.db import sessions
from app.core.models import Order, Service, User
from app.core.settings import config
from app.orders.engine import submit
from tests.test_foundation import fund
from tests.test_miniapp import TOKEN, signed


async def overview_for(user_id):
    stamp = int(datetime.now(UTC).timestamp())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.post(
            "/miniapp/api/overview", json={"init_data": signed(user_id=user_id, issued=stamp)}
        )


async def test_actual_order_and_credit_are_owner_scoped(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    await fund(11)
    await fund(22)
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).enabled = True
    mine = await submit(11, "echo", {"text": "mine"}, 100, "mine-1")
    theirs = await submit(22, "echo", {"text": "theirs"}, 100, "theirs-1")
    response = await overview_for(11)
    assert response.status_code == 200
    data = response.json()
    refs = [item["reference"] for item in data["orders"]]
    assert str(mine)[:8] in refs
    assert str(theirs)[:8] not in refs
    assert data["credit"] == {"available_sar": "9.00", "reserved_sar": "1.00"}
    assert any(item["slug"] == "csv_review" for item in data["services"])
    assert "test_credit" == data["payment_mode"]
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 2


async def test_banned_account_cannot_read_overview(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    await fund(11)
    async with sessions.begin() as db:
        (await db.get(User, 11)).banned = True
    response = await overview_for(11)
    assert response.status_code == 403
    assert response.headers["cache-control"] == "no-store"


async def test_stars_catalog_requires_explicit_price_and_never_exposes_sar_credit(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    monkeypatch.setattr(config(), "stars_enabled", True)
    await fund(11)
    async with sessions.begin() as db:
        row = await db.get(Service, "csv_review")
        row.enabled, row.price_stars = True, 8
        (await db.get(Service, "echo")).price_stars = None
    response = await overview_for(11)
    assert response.status_code == 200
    data = response.json()
    assert data["payment_mode"] == "stars"
    assert data["credit"] is None
    assert [(item["slug"], item["price"]) for item in data["services"]] == [("csv_review", 8)]


async def test_unsigned_identity_cannot_query_other_orders(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    await fund(11)
    await submit(11, "echo", {"text": "private"}, 100, "private-1")
    now = int(datetime.now(UTC).timestamp())
    raw = signed(user_id=11, issued=now).replace("%22id%22%3A11", "%22id%22%3A22")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/miniapp/api/overview", json={"init_data": raw})
    assert response.status_code == 401
