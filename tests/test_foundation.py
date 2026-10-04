import asyncio

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.orders.engine import register, submit
from app.services.base import ServiceError
from app.services.registry import registry
from app.wallet.ledger import (
    InsufficientFunds,
    WalletError,
    apply,
    balance,
    capture,
    halalas,
    release,
)
from app.workers.runner import execute_job


async def fund(user_id=1, amount=1000):
    await register(user_id)
    async with sessions.begin() as db:
        await apply(db, user_id, "credit", amount, f"seed:{user_id}")


class Delivery:
    def __init__(self):
        self.results = []

    async def send(self, user_id, order_id, result):
        self.results.append(result)


async def job_for(order_id):
    async with sessions() as db:
        return await db.scalar(select(Job.id).where(Job.order_id == order_id))


async def test_echo_full_flow_replay():
    await fund()
    order_id = await submit(1, "echo", {"text": "اختبار"}, 100, "order-1")
    assert await submit(1, "echo", {"text": "اختبار"}, 100, "order-1") == order_id
    async with sessions() as db:
        assert (await balance(db, 1)).reserved == 100
    delivery = Delivery()
    job = await job_for(order_id)
    await execute_job({"delivery": delivery}, str(job))
    await execute_job({"delivery": delivery}, str(job))
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "completed"
        assert (await balance(db, 1)).available == 900
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.results) == 1
    assert delivery.results[0].text == "اختبار"


async def test_failed_service_releases(monkeypatch):
    await fund()
    order_id = await submit(1, "echo", {"text": "x"}, 100, "fail")

    class Broken:
        async def run(self, inputs):
            raise ServiceError()

    monkeypatch.setattr(registry, "get", lambda *args: Broken())
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "failed"
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0


async def test_concurrent_orders_cannot_overspend():
    await fund()
    async with sessions.begin() as db:
        (await db.get(Service, "echo")).price_halala = 600
    results = await asyncio.gather(
        *[submit(1, "echo", {"text": "x"}, 600, f"c-{i}") for i in range(2)], return_exceptions=True
    )
    assert sum(isinstance(r, InsufficientFunds) for r in results) == 1
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved, funds.total) == (400, 600, 1000)


async def test_settlement_exclusive_and_credit_idempotent():
    await fund()
    async with sessions.begin() as db:
        await apply(db, 1, "credit", 1000, "seed:1")
    order_id = await submit(1, "echo", {"text": "x"}, 100, "reserve")
    async with sessions.begin() as db:
        await release(db, 1, 100, f"release:{order_id}", order_id)
        await release(db, 1, 100, f"release:{order_id}", order_id)
    async with sessions.begin() as db:
        with pytest.raises(WalletError):
            await capture(db, 1, 100, f"capture:{order_id}", order_id)
    async with sessions() as db:
        assert (await balance(db, 1)).available == 1000


async def test_ledger_immutable_in_database():
    await fund()
    for query in ("UPDATE wallet_ledger SET available_delta=9999", "DELETE FROM wallet_ledger"):
        with pytest.raises(DBAPIError):
            async with sessions.begin() as db:
                await db.execute(text(query))


async def test_registry_preserves_admin_overrides():
    async with sessions.begin() as db:
        row = await db.get(Service, "echo")
        row.price_halala, row.enabled = 999, False
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "echo")
        assert (row.price_halala, row.enabled) == (999, False)


@pytest.mark.parametrize("value", ["0", "-1", "1.001", "NaN", "Infinity", "bad"])
def test_invalid_money(value):
    with pytest.raises(WalletError):
        halalas(value)


async def test_health_endpoints():
    from app.api.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/health")).status_code == 200
        assert (await client.post("/webhooks/payment")).status_code == 501
        assert (await client.post("/webhooks/telegram", json={})).status_code == 403
