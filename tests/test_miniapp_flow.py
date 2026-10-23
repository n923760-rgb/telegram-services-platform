"""Database-backed Mini App privacy, activation and payment-view tests."""

from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import func, select

from app.api.main import app
from app.core.db import sessions
from app.core.models import Job, Ledger, Order, Service, User
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


@pytest.mark.parametrize("current_stars", [False, True])
async def test_order_windows_keep_older_active_work_and_historical_prices_private_and_read_only(
    monkeypatch, current_stars
):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    monkeypatch.setattr(config(), "stars_enabled", current_stars)
    monkeypatch.setattr(config(), "miniapp_bot_username", "ExampleBot")
    await fund(11)
    await fund(22)
    # Synthetic read fixtures: no submission, provider, Telegram or financial work.
    async with sessions.begin() as db:
        service = await db.get(Service, "echo")
        service.enabled, service.price_halala = False, 9900
        for i in range(1, 31):
            stars = i == 20
            db.add(
                Order(
                    id=UUID(f"{i:08x}-0000-0000-0000-000000000001"),
                    user_id=11 if i <= 20 else 22,
                    service_slug="echo",
                    price_halala=375,
                    payment_mode="stars" if stars else "test_credit",
                    price_stars=9 if stars else None,
                    terms_version="synthetic" if stars else None,
                    terms_hash="synthetic" if stars else None,
                    terms_snapshot={"ar": "synthetic", "en": "synthetic"} if stars else None,
                    idempotency_key=f"read-fixture-{i}",
                    input_hash="synthetic",
                    inputs={"text": "private payload"},
                    result={"text": "private output"},
                    status="waiting_confirmation"
                    if i == 10
                    else "queued"
                    if i < 10
                    else "future_status"
                    if i == 20
                    else "completed",
                    created_at=datetime(2026, 9 if i <= 10 else 10, 1, tzinfo=UTC),
                )
            )
    async with sessions() as db:
        before = [
            await db.scalar(select(func.count()).select_from(model))
            for model in (Order, Job, Ledger)
        ]
    response = await overview_for(11)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["orders_window"] == 8 and data["bot_url"] == "https://t.me/ExampleBot"
    rows = data["orders"]
    assert [item["reference"] for item in rows] == [
        f"{i:08x}" for i in [*range(20, 12, -1), *range(10, 2, -1)]
    ]
    assert any(item["status"] == "waiting_confirmation" for item in rows)
    assert rows[0]["amount"] == 9 and rows[0]["payment_mode"] == "stars"
    assert rows[0]["status"] == "unknown"
    assert all(
        item["amount"] == "3.75" and item["payment_mode"] == "test_credit" for item in rows[1:]
    )
    assert "private payload" not in response.text and "private output" not in response.text
    async with sessions() as db:
        after = [
            await db.scalar(select(func.count()).select_from(model))
            for model in (Order, Job, Ledger)
        ]
    assert before == after == [30, 0, 2]
