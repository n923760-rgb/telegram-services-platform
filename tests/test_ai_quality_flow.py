"""PostgreSQL lifecycle for automatic content review; model responses are fixtures."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostBudget, CostHold, CostUsage, Job, Ledger, Order, Setting, StarCharge
from app.ops.costs import keys
from app.orders.engine import submit
from app.providers.ai.gateway import AI
from app.providers.storage import OwnedStorage
from app.services.text_translation.test_service import GOOD, PLAN, SOURCE
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup
from tests.test_stars import pay, prepare
from tests.test_stars import stars as stars

ACCEPT = '{"accepted":true,"issues":[]}'
REJECT = '{"accepted":false,"issues":["meaning"]}'


async def reviewed(tmp_path, monkeypatch, responses):
    store, provider, delivery, ctx, price = await setup(
        "text_translation", responses, tmp_path, monkeypatch
    )

    def runtime(jid, uid):
        from types import SimpleNamespace

        return SimpleNamespace(
            ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
        )

    ctx["runtime_factory"] = runtime
    return store, provider, delivery, ctx, price


async def order(price):
    return await submit(
        1,
        "text_translation",
        {"text": SOURCE, "language": "en", "style": "formal"},
        price,
        "reviewed",
    )


@pytest.mark.parametrize("repair", [False, True])
async def test_reviewed_translation_captures_once_and_replays_cached_delivery(
    tmp_path, monkeypatch, repair
):
    responses = [json.dumps(PLAN), ACCEPT]
    if repair:
        responses = [json.dumps(PLAN), REJECT] + responses
    _, provider, delivery, ctx, price = await reviewed(tmp_path, monkeypatch, responses)
    oid = await order(price)
    jid = await job_for(oid)
    send = delivery.send

    async def offline(*args):
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", offline)
    await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        result = await db.get(Order, oid)
        assert result.result and result.status == "delivering"
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(delivery, "send", send)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert provider.calls == len(responses) and delivery.results[0].text == GOOD
    assert len(delivery.results) == 1 and dict(delivery.files)["translation.txt"].decode() == GOOD
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).available == 1000 - price
        assert (await balance(db, 1)).reserved == 0
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
        assert await db.scalar(select(func.count(CostUsage.id))) == len(responses)
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 1
        for key in keys(1):
            budget = await db.get(CostBudget, key)
            assert budget.reserved == 0 and budget.spent == Decimal(".004") * len(responses)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("failure", ["rejected", "schema", "cap", "uncertain"])
async def test_failed_review_releases_credit_and_retains_actual_provider_cost(
    tmp_path, monkeypatch, failure
):
    responses = [json.dumps(PLAN), REJECT, json.dumps(PLAN), REJECT]
    expected_calls, expected_cost, error = 4, Decimal(".016"), "provider_invalid"
    if failure == "schema":
        responses = [json.dumps(PLAN), "{}", "{}"]
        expected_calls, expected_cost = 3, Decimal(".012")
    elif failure == "cap":
        responses = [json.dumps(PLAN), "unused"]
        expected_calls, expected_cost, error = 1, Decimal(".004"), "job_cost_cap"
    elif failure == "uncertain":
        responses = [json.dumps(PLAN)]
        expected_calls, expected_cost, error = 2, Decimal(".004"), "service_failed"
    _, provider, delivery, ctx, price = await reviewed(tmp_path, monkeypatch, responses)
    if failure == "cap":
        async with sessions.begin() as db:
            db.add(Setting(key="MAX_JOB_COST_SAR", value={"value": ".013"}))
    oid = await order(price)
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert not delivery.results and not delivery.files and provider.calls == expected_calls
    async with sessions() as db:
        result = await db.get(Order, oid)
        assert result.status == "failed" and result.error_key == error and not result.result
        assert (await balance(db, 1)).available == 1000 and (await balance(db, 1)).reserved == 0
        assert (await db.get(Job, jid)).cost_sar == expected_cost
        holds = (await db.scalars(select(CostHold))).all()
        assert sum(hold.status == "uncertain" for hold in holds) == (failure == "uncertain")
        for key in keys(1):
            budget = await db.get(CostBudget, key)
            assert budget.spent == expected_cost
            assert budget.reserved == (Decimal(".01") if failure == "uncertain" else 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_paid_stars_review_failure_queues_one_refund_without_credit_conversion(
    stars, tmp_path, monkeypatch
):
    _, provider, delivery, ctx, _ = await reviewed(
        tmp_path, monkeypatch, [json.dumps(PLAN), REJECT, json.dumps(PLAN), REJECT]
    )
    from app.providers import runtime

    monkeypatch.setattr(runtime, "provider", lambda: provider)
    oid = await prepare("text_translation", {"text": SOURCE, "language": "en", "style": "formal"})
    await pay(oid, charge="quality-charge")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert provider.calls == 4 and not delivery.results
    async with sessions() as db:
        result = await db.get(Order, oid)
        charge = await db.get(StarCharge, "quality-charge")
        assert result.status == "failed" and result.price_stars == 20
        assert charge.state == "refund_pending"
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 1
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.order_id == oid)) == 0
        assert (await db.get(Job, jid)).cost_sar == Decimal(".016")
