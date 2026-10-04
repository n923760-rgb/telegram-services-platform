import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis

from app.core.db import sessions
from app.core.models import CostBudget, Job, Order, Service, Setting
from app.core.settings import config
from app.ops.admin import refund
from app.ops.circuit import evaluate
from app.ops.costs import keys, reserve_call, settle_call
from app.ops.notifier import Notifier
from app.ops.reports import report
from app.orders.engine import submit
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for


async def running(user=1):
    await fund(user)
    oid = await submit(user, "echo", {"text": "x"}, 100, "running")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        (await db.get(Job, jid)).status = "running"
    return oid, jid


async def test_cost_cap_concurrent_and_settlement_idempotent():
    _, jid = await running()
    async with sessions.begin() as db:
        db.add(Setting(key="MAX_DAILY_COST_SAR", value={"value": ".10"}))
    results = await asyncio.gather(
        *[reserve_call(jid, 1, Decimal(".06")) for _ in range(2)], return_exceptions=True
    )
    assert sum(isinstance(r, ServiceError) for r in results) == 1
    hold = next(r for r in results if not isinstance(r, Exception))
    await settle_call(hold, Decimal(".04"), 10, 20)
    await settle_call(hold, Decimal(".04"), 10, 20)
    async with sessions() as db:
        budget = await db.get(CostBudget, keys(1)[0])
        assert budget.spent == Decimal(".04") and budget.reserved == 0
        assert (await db.get(Job, jid)).cost_sar == Decimal(".04")


async def test_hit_cost_cap_blocks_order_before_reserve():
    await fund()
    async with sessions.begin() as db:
        db.add(CostBudget(key=keys(1)[0], spent=50, reserved=0))
    with pytest.raises(ServiceError, match="cost_cap"):
        await submit(1, "echo", {"text": "x"}, 100, "cap")
    async with sessions() as db:
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0


async def test_per_user_cost_and_job_caps():
    _, jid = await running()
    async with sessions.begin() as db:
        db.add(Setting(key="MAX_COST_PER_USER_PER_DAY", value={"value": ".01"}))
    with pytest.raises(ServiceError, match="user_cost_cap"):
        await reserve_call(jid, 1, Decimal(".02"))
    with pytest.raises(ServiceError, match="job_cost_cap"):
        await reserve_call(jid, 1, Decimal("3"))


async def test_refund_idempotent_and_bounded():
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "refund")
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    await asyncio.gather(refund(oid), refund(oid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "refunded"
        assert (await balance(db, 1)).available == 1000
    assert "1.00" in await report()


async def test_alert_deduplication_real_redis():
    redis = Redis.from_url(config().redis_url.get_secret_value())
    await redis.delete("alert:test:global")
    channel = AsyncMock()
    notifier = Notifier(redis, channel)
    results = await asyncio.gather(*[notifier.alert("test") for _ in range(8)])
    assert sum(results) == 1 and channel.send.await_count == 1
    assert await redis.ttl("alert:test:global") > 850
    await redis.aclose()


async def test_circuit_opens_releases_queued_reservations():
    for user in range(1, 8):
        await fund(user)
    ids = []
    for user in range(1, 8):
        ids.append(await submit(user, "echo", {"text": "x"}, 100, f"circuit-{user}"))
    async with sessions.begin() as db:
        for oid in ids[:5]:
            order = await db.get(Order, oid)
            from app.orders.engine import fail_locked

            await fail_locked(db, order)
    assert await evaluate("echo")
    assert not await evaluate("echo")
    async with sessions() as db:
        assert not (await db.get(Service, "echo")).enabled
        for user in (6, 7):
            assert (await balance(db, user)).reserved == 0


async def test_per_user_concurrency_limit():
    await fund()
    await submit(1, "echo", {"text": "x"}, 100, "a")
    await submit(1, "echo", {"text": "x"}, 100, "b")
    with pytest.raises(ServiceError, match="concurrent_limit"):
        await submit(1, "echo", {"text": "x"}, 100, "c")


async def test_user_cancellations_do_not_open_circuit():
    from app.orders.engine import fail_locked

    for user in range(1, 7):
        await fund(user)
        oid = await submit(user, "echo", {"text": "x"}, 100, f"cancel-{user}")
        async with sessions.begin() as db:
            order = await db.get(Order, oid)
            await fail_locked(db, order, "cancelled", cancelled=True)
    assert not await evaluate("echo")
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled


async def test_missing_information_does_not_open_circuit():
    from app.orders.engine import fail_locked

    for user in range(1, 7):
        await fund(user)
        oid = await submit(user, "echo", {"text": "x"}, 100, f"clarify-{user}")
        async with sessions.begin() as db:
            await fail_locked(db, await db.get(Order, oid), "needs_information")
    assert not await evaluate("echo")


async def test_failed_alert_send_can_be_retried():
    redis = Redis.from_url(config().redis_url.get_secret_value())
    await redis.delete("alert:test:global")
    channel = AsyncMock()
    channel.send.side_effect = OSError("transport unavailable")
    notifier = Notifier(redis, channel)
    with pytest.raises(OSError):
        await notifier.alert("test")
    channel.send.side_effect = None
    assert await notifier.alert("test")
    assert not await notifier.alert("test")
    await redis.aclose()


async def test_cost_provenance_is_saved_with_usage():
    from sqlalchemy import select

    from app.core.models import CostUsage

    _, jid = await running()
    hold = await reserve_call(jid, 1, Decimal(".1"))
    await settle_call(
        hold,
        Decimal(".02"),
        100,
        20,
        provider="fixture",
        model="fixture-v1",
        rates={"basis": "returned_tokens", "input": "1"},
    )
    async with sessions() as db:
        usage = await db.scalar(select(CostUsage))
        assert usage.provider == "fixture" and usage.model == "fixture-v1"
        assert usage.rate_snapshot["basis"] == "returned_tokens"


async def test_real_postgres_deadlock_retries_only_aborted_transaction():
    from sqlalchemy import select

    from app.core.models import User
    from app.core.transactions import transaction_retry

    await fund(1)
    await fund(2)
    ready = [asyncio.Event(), asyncio.Event()]
    attempts = [0, 0]

    @transaction_retry
    async def update(index, first, second):
        attempt = attempts[index]
        attempts[index] += 1
        async with sessions.begin() as db:
            await db.scalar(select(User).where(User.id == first).with_for_update())
            if attempt == 0:
                ready[index].set()
                await ready[1 - index].wait()
            await db.scalar(select(User).where(User.id == second).with_for_update())

    await asyncio.wait_for(asyncio.gather(update(0, 1, 2), update(1, 2, 1)), timeout=5)
    assert sum(attempts) == 3


async def test_wallet_key_cannot_be_reused_for_different_customer():
    from app.wallet.ledger import WalletError, apply

    await fund(1)
    await fund(2)
    async with sessions.begin() as db:
        await apply(db, 1, "credit", 100, "shared-credit-key")
    with pytest.raises(WalletError):
        async with sessions.begin() as db:
            await apply(db, 2, "credit", 100, "shared-credit-key")
    async with sessions() as db:
        assert (await balance(db, 1)).available == 1100
        assert (await balance(db, 2)).available == 1000


async def test_daily_report_failed_send_recovers_without_duplicate_success():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from app.ops.reports import daily_report, flush_reports

    redis = Redis.from_url(config().redis_url.get_secret_value())
    day = datetime.now(ZoneInfo("Asia/Riyadh")).date()
    await redis.delete(f"report:pending:{day}", f"report:sent:{day}", f"report:claim:{day}")
    channel = AsyncMock()
    channel.send.side_effect = OSError("offline")
    ctx = {"redis": redis, "notifier": Notifier(redis, channel)}
    with pytest.raises(OSError):
        await daily_report(ctx)
    assert await redis.exists(f"report:pending:{day}")
    channel.send.side_effect = None
    await flush_reports(ctx)
    assert not await redis.exists(f"report:pending:{day}")
    assert await redis.exists(f"report:sent:{day}")
    await daily_report(ctx)
    assert channel.send.await_count == 2
    await redis.aclose()


async def test_report_shows_uncertain_provider_exposure():
    from app.ops.costs import uncertain_call

    _, jid = await running()
    hold = await reserve_call(jid, 1, Decimal(".1"))
    await uncertain_call(hold)
    assert "0.100000" in await report()
