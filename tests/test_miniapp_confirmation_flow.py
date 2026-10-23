"""Real PostgreSQL/Redis financial admission, replay and cross-channel races."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.api.main import app
from app.core.db import sessions
from app.core.models import Job, Ledger, Order, Service, StarCheckout
from app.core.settings import config
from app.miniapp import confirmation
from app.orders.engine import fail_locked
from app.orders.locking import lock_order
from app.services.registry import registry
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix
from tests.test_foundation import fund
from tests.test_miniapp import signed
from tests.test_miniapp_drafts_flow import OWNER
from tests.test_miniapp_drafts_flow import shared as shared


@pytest.fixture
async def confirm_shared(shared, monkeypatch):
    monkeypatch.setattr(config(), "miniapp_confirm_enabled", True)
    return shared


async def prepare(shared):
    call = shared[0]
    first = (await call("open", slug="echo")).json()["draft"]
    assert first["confirmation"] is None
    saved = await call(
        "answer", revision=first["revision"], operation=uuid4().hex, value="Synthetic request"
    )
    assert saved.status_code == 200
    return saved.json()["draft"]


async def confirm(token, *, user=OWNER, accepted=True, headers=None, extra=None):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        return await client.post(
            "/miniapp/api/confirm",
            headers={"Origin": "https://test", **(headers or {})},
            json={
                "init_data": signed(user_id=user, issued=int(datetime.now(UTC).timestamp())),
                "token": token,
                "accepted": accepted,
                **(extra or {}),
            },
        )


async def counts():
    async with sessions() as db:
        return {
            model.__name__: await db.scalar(select(func.count()).select_from(model))
            for model in (Order, Job, StarCheckout)
        }


async def test_explicit_consent_and_concurrent_retry_reserve_exactly_once(confirm_shared):
    view = await prepare(confirm_shared)
    token = view["confirmation"]["token"]
    assert (await confirm(token, accepted=False)).status_code == 400
    assert await counts() == {"Order": 0, "Job": 0, "StarCheckout": 0}
    a, b = await asyncio.gather(confirm(token), confirm(token))
    assert a.status_code == b.status_code == 200 and a.json() == b.json()
    assert await confirm_shared[3].get_data() == {}
    assert await counts() == {"Order": 1, "Job": 1, "StarCheckout": 0}
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 100
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "reserve")) == 1


async def test_bot_and_miniapp_confirmation_share_the_same_purchase(confirm_shared):
    call, message, callback, _, transport, _, _ = confirm_shared
    await prepare(confirm_shared)
    await message("/start request_echo")
    button = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    view = (await call()).json()["draft"]
    response, _ = await asyncio.gather(confirm(view["confirmation"]["token"]), callback(button))
    assert response.status_code == 200
    assert (await counts())["Order"] == 1
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 100


@pytest.mark.parametrize("change", ["price", "version", "disabled", "payment", "provider", "flag"])
async def test_current_admission_and_rollout_gates_prevent_new_purchase(
    confirm_shared, monkeypatch, change
):
    view = await prepare(confirm_shared)
    if change in {"price", "version", "disabled"}:
        async with sessions.begin() as db:
            row = await db.get(Service, "echo")
            if change == "price":
                row.price_halala = 200
            if change == "version":
                row.version = "changed"
            if change == "disabled":
                row.enabled = False
    if change == "payment":
        monkeypatch.setattr(config(), "stars_enabled", True)
    if change == "provider":
        monkeypatch.setattr(
            registry.types["echo"], "needs_ai", classmethod(lambda cls, inputs: True)
        )
        monkeypatch.setattr(config(), "ai_enabled", False)
    if change == "flag":
        monkeypatch.setattr(config(), "miniapp_confirm_enabled", False)
    response = await confirm(view["confirmation"]["token"])
    assert response.status_code == (404 if change == "flag" else 409)
    assert (await counts())["Order"] == 0
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 0


async def test_insufficient_test_credit_does_not_leave_order_or_job(confirm_shared):
    async with sessions.begin() as db:
        (await db.get(Service, "echo")).price_halala = 2000
    view = await prepare(confirm_shared)
    response = await confirm(view["confirmation"]["token"])
    assert response.status_code == 409 and response.json()["detail"] == "insufficient"
    assert await counts() == {"Order": 0, "Job": 0, "StarCheckout": 0}


@pytest.mark.parametrize("where", ["submit", "cleanup"])
async def test_ambiguous_success_recovers_durable_receipt_without_double_reservation(
    confirm_shared, monkeypatch, where
):
    view = await prepare(confirm_shared)
    token = view["confirmation"]["token"]
    actual = confirmation.submit if where == "submit" else confirmation.clear_accepted

    async def failed(*args, **kwargs):
        if where == "submit":
            await actual(*args, **kwargs)
        raise OSError("synthetic acknowledgement lost")

    monkeypatch.setattr(confirmation, "submit" if where == "submit" else "clear_accepted", failed)
    assert (await confirm(token)).status_code == 503
    assert (await counts())["Order"] == 1
    monkeypatch.setattr(confirmation, "submit" if where == "submit" else "clear_accepted", actual)
    assert (await confirm(token)).status_code == 200
    assert await confirm_shared[3].get_data() == {}
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 100


async def test_replayed_receipt_preserves_newer_draft_and_reports_terminal_status(confirm_shared):
    call, _, _, state, _, _, _ = confirm_shared
    view = await prepare(confirm_shared)
    token = view["confirmation"]["token"]
    first = await confirm(token)
    assert first.status_code == 200
    async with sessions.begin() as db:
        order = await db.scalar(select(Order))
        await fail_locked(db, await lock_order(db, order.id))
    await call("open", slug="echo")
    newer = await state.get_data()
    replay = await confirm(token)
    assert replay.status_code == 200 and replay.json()["receipt"]["status"] == "failed"
    assert await state.get_data() == newer
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "release")) == 1


async def test_stale_or_missing_draft_and_another_owner_cannot_purchase(confirm_shared):
    view = await prepare(confirm_shared)
    token = view["confirmation"]["token"]
    other = OWNER + 1
    await fund(other)
    assert (await confirm(token, user=other)).status_code == 409
    await confirm_shared[5].redis.delete(f"rate:{other}")
    edited = await confirm_shared[0](
        "edit", revision=view["revision"], operation=uuid4().hex, index=0
    )
    assert edited.status_code == 200
    assert (await confirm(token)).status_code == 409
    await confirm_shared[3].clear()
    assert (await confirm(token)).status_code == 409
    assert (await counts())["Order"] == 0


async def test_cross_origin_forged_identity_and_extra_financial_fields_cannot_submit(
    confirm_shared,
):
    view = await prepare(confirm_shared)
    token = view["confirmation"]["token"]
    assert (await confirm(token, headers={"Origin": "https://other.test"})).status_code == 403
    assert (await confirm(token, extra={"init_data": "unsigned"})).status_code == 401
    assert (await confirm(token, extra={"price": 1})).status_code == 400
    assert (await counts())["Order"] == 0
