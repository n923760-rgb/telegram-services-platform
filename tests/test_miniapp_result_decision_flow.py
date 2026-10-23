"""Real PostgreSQL/Redis consent, settlement and competing bot/API decisions."""

import asyncio
from datetime import UTC, datetime

import httpx
import pytest
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError

from app.api.main import app
from app.core.db import sessions
from app.core.models import Job, Ledger, Order
from app.core.settings import config
from app.miniapp import result_review
from app.orders.engine import confirm_structure, submit
from app.providers.storage import LocalStorage
from app.services.base import Result, ServiceError
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for
from tests.test_miniapp import TOKEN, signed
from tests.test_miniapp_result_review_unit import png


@pytest.fixture
async def decision(monkeypatch, tmp_path):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    monkeypatch.setattr(config(), "miniapp_confirm_enabled", True)
    monkeypatch.setattr(config(), "stars_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund(11)
    oid = await submit(11, "echo", {"text": "Private input"}, 100, "review-decision")
    store = LocalStorage(tmp_path)
    image = store.save(11, "preview.png", png(), "image/png")
    original = store.save(11, "result.docx", b"cached original", "application/octet-stream")
    result = Result(
        needs_confirmation=True,
        continuation={"next": "step"},
        review_details="Full review",
        preview_artifacts=[image],
    )
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status, order.result = "waiting_confirmation", result.model_dump(mode="json")
    redis = RedisStorage.from_url(config().redis_url.get_secret_value())
    key = StorageKey(bot_id=12345, chat_id=11, user_id=11)
    names = [redis.key_builder.build(key, p) for p in ("state", "data", "lock")] + ["rate:11"]
    await redis.redis.delete(*names)
    await redis.set_state(key, "support")
    await redis.set_data(key, {"saved": "unrelated session"})
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:

        async def read():
            response = await client.post(
                "/miniapp/api/result-review",
                headers={"Origin": "https://test"},
                json={
                    "init_data": signed(user_id=11, issued=int(datetime.now(UTC).timestamp())),
                    "order_id": str(oid),
                },
            )
            assert response.status_code == 200
            return response.json()["review"]["decision"]["token"]

        async def post(token, approved=True):
            return await client.post(
                "/miniapp/api/result-decision",
                headers={"Origin": "https://test"},
                json={
                    "init_data": signed(user_id=11, issued=int(datetime.now(UTC).timestamp())),
                    "token": token,
                    "approved": approved,
                    "accepted": True,
                },
            )

        try:
            yield oid, read, post, store, original
            assert await redis.get_state(key) == "support"
            assert await redis.get_data(key) == {"saved": "unrelated session"}
        finally:
            await redis.redis.delete(*names)
            await redis.close()


async def ledger_state(oid):
    async with sessions() as db:
        order = await db.get(Order, oid)
        funds = await balance(db, 11)
        kinds = list(await db.scalars(select(Ledger.kind).where(Ledger.order_id == oid)))
        assert await db.scalar(select(func.count(Job.id)).where(Job.order_id == oid)) == 1
        return order.status, funds.available, funds.reserved, sorted(kinds)


@pytest.mark.parametrize("approve", [False, True])
async def test_decision_applies_once_and_preserves_reservation_contract(decision, approve):
    oid, read, post, *_ = decision
    token = await read()
    response = await post(token, approve)
    assert response.status_code == 200 and response.json()["receipt"]["approved"] is approve
    assert (await post(token, approve)).status_code == 409
    assert (await post(token, not approve)).status_code == 409
    assert await ledger_state(oid) == (
        ("queued", 900, 100, ["reserve"])
        if approve
        else ("cancelled", 1000, 0, ["release", "reserve"])
    )
    if approve:
        async with sessions() as db:
            order = await db.get(Order, oid)
            assert order.inputs["__continuation"] == {"next": "step"} and order.result is None


async def test_prepared_approval_delivers_cached_file_without_service_execution(
    decision, monkeypatch
):
    oid, read, post, _, original = decision
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.result = {
            **order.result,
            "prepared_delivery": True,
            "artifacts": [original.model_dump(mode="json")],
        }
    token = await read()
    assert (await post(token)).status_code == 200
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    assert delivery.results[0].artifacts == [original]
    assert await ledger_state(oid) == ("completed", 900, 0, ["capture", "reserve"])


@pytest.mark.parametrize("changed", ["result", "round", "phase"])
async def test_stale_review_never_applies_to_new_snapshot(decision, changed):
    oid, read, post, *_ = decision
    token = await read()
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        if changed == "result":
            order.result = {**order.result, "review_details": "Changed review"}
        elif changed == "round":
            (await db.scalar(select(Job).where(Job.order_id == oid))).attempts += 1
        else:
            order.status = "queued"
    assert (await post(token)).status_code == 409
    assert (await ledger_state(oid))[1:] == (900, 100, ["reserve"])


async def test_database_preserves_payment_contract_after_review(decision):
    oid, read, post, *_ = decision
    token = await read()
    with pytest.raises(DBAPIError, match="order payment contract is immutable"):
        async with sessions.begin() as db:
            (await db.get(Order, oid)).payment_mode = "stars"
    async with sessions() as db:
        assert (await db.get(Order, oid)).payment_mode == "test_credit"
    assert (await post(token, False)).status_code == 200
    assert await ledger_state(oid) == ("cancelled", 1000, 0, ["release", "reserve"])


async def test_competing_http_approve_cancel_has_one_winner(decision):
    oid, read, post, *_ = decision
    token = await read()
    responses = await asyncio.gather(post(token, True), post(token, False))
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert await ledger_state(oid) in (
        ("queued", 900, 100, ["reserve"]),
        ("cancelled", 1000, 0, ["release", "reserve"]),
    )


async def test_bot_and_http_share_locked_decision_contract(decision):
    oid, read, post, *_ = decision
    token = await read()
    results = await asyncio.gather(
        post(token), confirm_structure(oid, 11, False), return_exceptions=True
    )
    assert (results[0].status_code == 200) != (results[1] is None)
    assert results[1] is None or isinstance(results[1], ServiceError)
    assert await ledger_state(oid) in (
        ("queued", 900, 100, ["reserve"]),
        ("cancelled", 1000, 0, ["release", "reserve"]),
    )


async def test_lost_postcommit_response_requires_refresh_without_repeat_apply(
    decision, monkeypatch
):
    oid, read, post, *_ = decision
    token = await read()
    original = result_review.confirm_structure

    async def lose_response(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("synthetic postcommit failure")

    monkeypatch.setattr(result_review, "confirm_structure", lose_response)
    assert (await post(token, False)).status_code == 503
    assert (await post(token, False)).status_code == 409
    assert await ledger_state(oid) == ("cancelled", 1000, 0, ["release", "reserve"])
