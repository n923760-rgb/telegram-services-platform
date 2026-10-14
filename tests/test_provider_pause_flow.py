import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select, update

from app.builders.schema import StrictModel
from app.core.db import sessions
from app.core.models import (
    CostBudget,
    CostHold,
    CostUsage,
    Job,
    Ledger,
    Order,
    Service,
    Setting,
    StarCharge,
    StarCheckout,
)
from app.core.settings import config
from app.ops.admin import set_service
from app.ops.costs import keys, reserve_call, uncertain_call
from app.ops.readiness import ai_configuration
from app.orders.engine import submit
from app.payments.stars import payload, pre_checkout
from app.providers.ai.gateway import AI
from app.services.base import ServiceError
from app.wallet.ledger import balance
from tests.test_foundation import fund
from tests.test_operations import running
from tests.test_stars import prepare
from tests.test_stars import stars as stars


class Outcome(StrictModel):
    ok: bool


@pytest.mark.parametrize("value", [{"value": 0}, {"value": None}, {}, []])
async def test_malformed_pause_blocks_ai_before_credit_but_direct_remains_available(
    monkeypatch, value
):
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    await set_service("text_to_pdf", enabled=True)
    async with sessions.begin() as db:
        price = (await db.get(Service, "text_to_pdf")).price_halala
        db.add(Setting(key="PROVIDER_PAUSED", value=value))
    with pytest.raises(ServiceError, match="provider_config"):
        await submit(1, "text_to_pdf", {"text": "Source", "mode": "smart"}, price, "blocked")
    async with sessions() as db:
        assert await ai_configuration(db) == "paused"
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "reserve")) == 0
        assert (await balance(db, 1)).available == 1000
        assert (await db.get(Setting, "PROVIDER_PAUSED")).value == value
    oid = await submit(1, "text_to_pdf", {"text": "Source", "mode": "direct"}, price, "direct")
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "queued"
        assert await db.scalar(select(func.count(CostHold.id))) == 0


@pytest.mark.parametrize("value", [{"value": 0}, {"value": None}, {}, []])
async def test_malformed_pause_blocks_stars_submission_and_stale_precheckout(
    stars, monkeypatch, value
):
    monkeypatch.setattr(config(), "ai_enabled", True)
    oid = await prepare("text_to_pdf", {"text": "Source", "mode": "smart"})
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value=value))
    with pytest.raises(ServiceError, match="provider_config"):
        await prepare("text_to_pdf", {"text": "Source", "mode": "smart"}, key="blocked")
    with pytest.raises(ServiceError, match="provider_config"):
        await pre_checkout(1, payload(oid), "XTR", 20, "stale-checkout")
    async with sessions() as db:
        assert (await db.get(StarCheckout, oid)).query_id is None
        assert (await db.get(Order, oid)).status == "awaiting_payment"
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id))) == 0


@pytest.mark.parametrize("value", [{"value": 0}, {"value": None}, {}, []])
async def test_malformed_pause_blocks_concurrent_gateway_calls_and_preserves_unknown(value):
    _, jid = await running()
    unknown = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(unknown)
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value=value))
    provider = AsyncMock()
    provider.upper_bound = lambda *args: Decimal(".001")
    ai = AI(provider, jid, 1)
    results = await asyncio.gather(
        *[ai.extract(Outcome, "Synthetic") for _ in range(2)], return_exceptions=True
    )
    assert all(
        isinstance(result, ServiceError) and result.key == "provider_usage" for result in results
    )
    provider.extract_from_text.assert_not_awaited()
    async with sessions() as db:
        assert (await db.get(CostHold, unknown)).status == "uncertain"
        assert await db.scalar(select(func.count(CostHold.id))) == 1
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        budget = await db.get(CostBudget, keys(1)[0])
        assert budget.reserved == Decimal(".01") and budget.spent == 0
        assert (await db.get(Job, jid)).cost_sar == 0
        assert (await balance(db, 1)).reserved == 100
    # An explicit operator correction permits new reservations, never clears old exposure.
    async with sessions.begin() as db:
        # Assigning JSON 0 -> false through ORM dirty comparison sees equal Python
        # dictionaries (0 == False). Model an explicit operator SQL correction.
        await db.execute(
            update(Setting).where(Setting.key == "PROVIDER_PAUSED").values(value={"value": False})
        )
    async with sessions() as db:
        assert (await db.get(Setting, "PROVIDER_PAUSED")).value["value"] is False
    new_hold = await reserve_call(jid, 1, Decimal(".001"))
    async with sessions() as db:
        assert (await db.get(CostHold, new_hold)).status == "open"
        assert (await db.get(CostHold, unknown)).status == "uncertain"
