import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import Order, OrderCompletion, User
from app.orders import completions
from app.orders.engine import complete_locked, submit
from app.orders.locking import lock_order
from app.services.base import Result, ServiceError
from app.services.completion import Completion
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for


def output():
    return Result(
        text="Prepared draft available after processing",
        completion=Completion(kind="example_v1", payload={"name": "مدى", "source": "00123"}),
    )


async def pending():
    await fund()
    return await submit(1, "echo", {"text": "source"}, 100, "completion")


async def completed(monkeypatch):
    order_id = await pending()
    run = AsyncMock(return_value=output())
    monkeypatch.setattr(registry, "get", lambda *args: SimpleNamespace(run=run))
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    return order_id, run


async def test_worker_handoff_survives_result_retention_and_is_consumed_once(monkeypatch):
    order_id, run = await completed(monkeypatch)
    await completions.purge()  # Fresh pending data must survive an ordinary sweep.
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    async with sessions.begin() as db:
        order = await db.get(Order, order_id)
        assert order.status == "completed" and order.files_deleted
        row = await db.get(OrderCompletion, order_id)
        assert row.owner_id == 1 and row.payload["source"] == "00123"
        # Ordinary result expiry is independent of the pending DB handoff.
        order.inputs, order.result = {}, None
        assert (await balance(db, 1)).reserved == 0
        assert (await balance(db, 1)).available == 900

    async def apply(db, order, payload):
        assert order.user_id == 1 and payload == output().completion.payload
        user = await db.get(User, order.user_id)
        user.language = "en"

    assert await completions.consume(order_id, 1, "example_v1", apply)
    assert not await completions.consume(order_id, 1, "example_v1", apply)
    assert run.await_count == 1
    async with sessions() as db:
        row = await db.get(OrderCompletion, order_id)
        assert row.state == "applied" and row.payload is None
        assert (await db.get(User, 1)).language == "en"


async def test_delivery_retry_reuses_generation_and_only_completes_one_handoff(monkeypatch):
    order_id = await pending()
    run = AsyncMock(return_value=output())
    monkeypatch.setattr(registry, "get", lambda *args: SimpleNamespace(run=run))
    delivery = SimpleNamespace(send=AsyncMock(side_effect=[OSError("synthetic"), None]))
    job_id = await job_for(order_id)
    await execute_job({"delivery": delivery}, str(job_id))
    from app.core.models import Job

    async with sessions.begin() as db:
        assert await db.get(OrderCompletion, order_id) is None
        (await db.get(Job, job_id)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job({"delivery": delivery}, str(job_id))
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "completed"
        assert await db.scalar(select(func.count()).select_from(OrderCompletion)) == 1
    assert run.await_count == 1 and delivery.send.await_count == 2


async def test_ordinary_service_completion_does_not_create_handoff():
    order_id = await pending()
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "completed"
        assert (await balance(db, 1)).available == 900
        assert await db.scalar(select(func.count()).select_from(OrderCompletion)) == 0


async def test_handoff_and_capture_roll_back_together(monkeypatch):
    order_id = await pending()
    from app.orders import engine

    async def broken_capture(db, order):
        assert await db.get(OrderCompletion, order.id)
        raise RuntimeError("synthetic capture failure")

    monkeypatch.setattr(engine, "capture_order", broken_capture)
    with pytest.raises(RuntimeError):
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            order.status, order.result = "delivering", output().model_dump(mode="json")
            await complete_locked(db, order)
    async with sessions() as db:
        assert await db.get(OrderCompletion, order_id) is None
        assert (await db.get(Order, order_id)).status == "queued"
        assert (await balance(db, 1)).reserved == 100


async def test_handler_failure_rolls_back_writes_and_preserves_retry(monkeypatch):
    order_id, _ = await completed(monkeypatch)

    async def fail(db, order, payload):
        (await db.get(User, 1)).language = "en"
        await db.flush()
        raise RuntimeError("synthetic handler failure")

    with pytest.raises(RuntimeError):
        await completions.consume(order_id, 1, "example_v1", fail)
    async with sessions() as db:
        assert (await db.get(User, 1)).language == "ar"
        assert (await db.get(OrderCompletion, order_id)).payload == output().completion.payload
    handler = AsyncMock()
    assert await completions.consume(order_id, 1, "example_v1", handler)
    assert handler.await_count == 1


async def test_concurrent_consumers_apply_exactly_once(monkeypatch):
    order_id, _ = await completed(monkeypatch)
    handler = AsyncMock()
    outcomes = await asyncio.gather(
        *[completions.consume(order_id, 1, "example_v1", handler) for _ in range(3)]
    )
    assert outcomes.count(True) == 1 and outcomes.count(False) == 2
    assert handler.await_count == 1


async def test_ownership_kind_ban_refund_and_unfinished_order_reject(monkeypatch):
    order_id = await pending()
    handler = AsyncMock()
    with pytest.raises(ServiceError):
        await completions.consume(order_id, 1, "example_v1", handler)
    run = AsyncMock(return_value=output())
    monkeypatch.setattr(registry, "get", lambda *args: SimpleNamespace(run=run))
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    for owner, kind in [(2, "example_v1"), (1, "wrong_v1")]:
        with pytest.raises(ServiceError):
            await completions.consume(order_id, owner, kind, handler)
    async with sessions.begin() as db:
        (await db.get(User, 1)).banned = True
    with pytest.raises(ServiceError):
        await completions.consume(order_id, 1, "example_v1", handler)
    async with sessions.begin() as db:
        (await db.get(User, 1)).banned = False
        (await db.get(Order, order_id)).status = "refunded"
    with pytest.raises(ServiceError):
        await completions.consume(order_id, 1, "example_v1", handler)
    await completions.purge()
    async with sessions() as db:
        row = await db.get(OrderCompletion, order_id)
        assert row.state == "discarded" and row.payload is None
    handler.assert_not_awaited()


async def test_expiry_scrubs_unhandled_data_and_never_extends_deadline(monkeypatch):
    order_id, _ = await completed(monkeypatch)
    async with sessions() as db:
        deadline = (await db.get(OrderCompletion, order_id)).expires_at

    class Future(datetime):
        @classmethod
        def now(cls, tz=None):
            return deadline + timedelta(seconds=1)

    monkeypatch.setattr(completions, "datetime", Future)
    handler = AsyncMock()
    with pytest.raises(ServiceError):
        await completions.consume(order_id, 1, "example_v1", handler)
    await completions.purge()
    await completions.purge()
    async with sessions.begin() as db:
        order = await lock_order(db, order_id)
        # Simulate replay at the internal staging boundary, not a new completion.
        order.status = "delivering"
        await completions.stage_locked(db, order)
        row = await db.get(OrderCompletion, order_id)
        assert row.expires_at == deadline and row.state == "discarded" and row.payload is None
    handler.assert_not_awaited()


async def test_changed_replay_and_direct_sql_rewrite_reject(monkeypatch):
    order_id, _ = await completed(monkeypatch)
    with pytest.raises(ServiceError):
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            changed = output()
            changed.completion.payload["source"] = "changed"
            order.status, order.result = "delivering", changed.model_dump(mode="json")
            await completions.stage_locked(db, order)
    for assignment in [
        "kind='changed'",
        "expires_at=expires_at+interval '1 day'",
        "payload='{}'::json",
    ]:
        with pytest.raises(DBAPIError):
            async with sessions.begin() as db:
                await db.execute(text(f"UPDATE order_completions SET {assignment}"))
    assert await completions.consume(order_id, 1, "example_v1", AsyncMock())
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            await db.execute(
                text("UPDATE order_completions SET state='pending', payload='{}'::json")
            )
