"""Disposable PostgreSQL activation intent, cancellation and Stars recovery."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import (
    Job,
    Ledger,
    Order,
    Service,
    ServiceActivationChange,
    ServiceActivationTask,
    StarCharge,
)
from app.core.settings import config
from app.ops import activation
from app.ops.admin import set_service
from app.orders.engine import complete_locked, submit
from app.orders.locking import lock_order
from app.payments.recovery import refunds
from app.payments.stars import payload, receive
from app.services.base import ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from tests.test_admin_prices import Conversation
from tests.test_admin_prices import owner as owner
from tests.test_foundation import fund
from tests.test_stars import Provider, pay, prepare
from tests.test_stars import stars as stars


async def propose(enabled=False, slug="echo", actor=7):
    return activation.digest(await activation.preview(slug, enabled, actor_id=actor))


async def commit(enabled=False, slug="echo", actor=7, key=None, expected=None):
    return await activation.change_activation(
        slug,
        enabled,
        actor_id=actor,
        expected_hash=expected or await propose(enabled, slug, actor),
        change_id=key or uuid4(),
    )


async def test_atomic_flag_audit_replay_and_prices_preserved(owner):
    await set_service("echo", stars=37, price=777)
    expected, key = await propose(), uuid4()
    await asyncio.gather(commit(key=key, expected=expected), commit(key=key, expected=expected))
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "echo")
        audit = await db.get(ServiceActivationChange, key)
        assert not row.enabled and row.price_halala == 777 and row.price_stars == 37
        assert audit.actor_id == 7 and audit.old_enabled and not audit.new_enabled
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 1
        assert await db.scalar(select(func.count()).select_from(ServiceActivationTask)) == 0
    await commit(True)
    await commit(key=key, expected=expected)
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled  # Old operation cannot re-disable.


@pytest.mark.parametrize("change", ["price", "stars", "version", "flag", "orders"])
async def test_snapshot_change_requires_new_review(owner, change):
    expected = await propose()
    if change == "orders":
        await fund()
        await submit(1, "echo", {"text": "original"}, 100, "new")
    else:
        async with sessions.begin() as db:
            row = await db.get(Service, "echo")
            if change == "price":
                row.price_halala = 150
            elif change == "stars":
                row.price_stars = 25
            elif change == "version":
                row.version = "old"
            else:
                row.enabled = False
    with pytest.raises(ServiceError, match="admin_activation_changed"):
        await commit(expected=expected)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0
        assert (await db.get(Service, "echo")).enabled == (change != "flag")


@pytest.mark.parametrize("change", ["actor", "target", "hash", "service"])
async def test_operation_id_is_bound_to_full_payload(owner, change):
    expected, key = await propose(), uuid4()
    await commit(expected=expected, key=key)
    with pytest.raises(ServiceError, match="invalid_request"):
        await commit(
            expected="0" * 64 if change == "hash" else expected,
            key=key,
            enabled=change == "target",
            actor=8 if change == "actor" else 7,
            slug="images_to_pdf" if change == "service" else "echo",
        )


async def test_revocation_is_checked_before_mutation(owner):
    expected = await propose()
    config().admin_ids = []
    with pytest.raises(ServiceError, match="not_allowed"):
        await commit(expected=expected)
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0


@pytest.mark.parametrize(
    "sql",
    ["UPDATE service_activation_changes SET actor_id=8", "DELETE FROM service_activation_changes"],
)
async def test_activation_audit_cannot_be_edited_or_deleted(owner, sql):
    await commit()
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            await db.execute(text(sql))


async def test_credit_cancellation_is_durable_and_concurrent_recovery_releases_once(owner):
    await fund()
    oid = await submit(1, "echo", {"text": "literal"}, 100, "credit")
    key = await commit()
    async with sessions() as db:
        assert (await balance(db, 1)).reserved == 100  # Flag commit is not settlement.
        assert (await db.get(ServiceActivationTask, key)).completed_at is None
    with pytest.raises(ServiceError, match="admin_activation_pending"):
        await propose(True)
    await asyncio.gather(activation.settle_activations({}), activation.settle_activations({}))
    await activation.settle_activations({})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await db.scalar(select(Job).where(Job.order_id == oid))).status == "cancelled"
        assert (await db.get(ServiceActivationTask, key)).completed_at is not None
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert (
            await db.scalar(
                select(func.count()).select_from(Ledger).where(Ledger.kind == "release")
            )
            == 1
        )
    await commit(True)


async def test_partial_recovery_crash_resumes_without_double_release(owner, monkeypatch):
    await fund()
    for i in range(2):
        await submit(1, "echo", {"text": "literal"}, 100, f"credit-{i}")
    key = await commit()
    original = activation.cancel_target

    async def crash_after_commit(oid):
        await original(oid)
        raise RuntimeError("fixture crash after settlement commit")

    monkeypatch.setattr(activation, "cancel_target", crash_after_commit)
    with pytest.raises(RuntimeError):
        await activation.settle_activations({})
    async with sessions() as db:
        assert (await db.get(ServiceActivationTask, key)).completed_at is None
    monkeypatch.setattr(activation, "cancel_target", original)
    await activation.settle_activations({})
    async with sessions() as db:
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0
        assert (
            await db.scalar(
                select(func.count()).select_from(Ledger).where(Ledger.kind == "release")
            )
            == 2
        )


async def test_frozen_intent_does_not_cancel_new_orders_after_other_route_reenables(owner):
    await fund()
    old = await submit(1, "echo", {"text": "old"}, 100, "old")
    expected, key = await propose(), uuid4()
    await commit(expected=expected, key=key)
    await set_service(
        "echo", enabled=True
    )  # Existing operator route, not an advertised UI shortcut.
    new = await submit(1, "echo", {"text": "new"}, 100, "new")
    await commit(expected=expected, key=key)
    await activation.settle_activations({})
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled
        assert (await db.get(Order, old)).status == "cancelled"
        assert (await db.get(Order, new)).status == "queued"
        assert (await balance(db, 1)).reserved == 100


async def test_concurrently_completed_order_is_not_refunded_by_old_cancel_intent(owner):
    await fund()
    oid = await submit(1, "echo", {"text": "original"}, 100, "complete")
    await commit()
    async with sessions.begin() as db:
        order = await lock_order(db, oid)
        order.status = "delivering"
        await complete_locked(db, order)
    await activation.settle_activations({})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).available == 900
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Ledger)
                .where(Ledger.kind.in_(["release", "refund"]))
            )
            == 0
        )


async def test_disable_and_admission_race_never_creates_unreviewed_cancel_target(owner):
    await fund()
    expected = await propose()
    outcomes = await asyncio.gather(
        commit(expected=expected),
        submit(1, "echo", {"text": "racing"}, 100, "race"),
        return_exceptions=True,
    )
    assert sum(isinstance(x, ServiceError) for x in outcomes) == 1
    async with sessions() as db:
        service = await db.get(Service, "echo")
        orders = list((await db.scalars(select(Order))).all())
        assert (service.enabled and len(orders) == 1) or (not service.enabled and not orders)


async def test_stars_cancel_is_pending_until_independent_confirmation(stars, owner):
    oid = await prepare()
    await pay(oid)
    evidence = await activation.preview("echo", False, actor_id=7)
    assert activation.totals(evidence)["paid_stars"] == 20
    key = await commit()
    await activation.settle_activations({})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await db.get(StarCharge, "charge")).state == "refund_pending"
        assert (await db.get(ServiceActivationTask, key)).completed_at is not None
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 0
    provider = Provider(True)
    await refunds({"stars": provider})
    await refunds({"stars": provider})
    assert provider.calls == [(1, "charge")]
    async with sessions() as db:
        assert (await db.get(StarCharge, "charge")).state == "refunded"


async def test_late_payment_after_unpaid_cancel_is_recorded_and_refundable(stars, owner):
    oid = await prepare()
    evidence = await activation.preview("echo", False, actor_id=7)
    assert activation.totals(evidence)["unpaid"] == 1
    await commit()
    await activation.settle_activations({})
    await receive(1, payload(oid), "XTR", 20, "late")
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await db.get(StarCharge, "late")).state == "refund_pending"
        assert await db.scalar(select(func.count()).select_from(Job)) == 0


async def test_payment_arrival_invalidates_preview_without_refunding(stars, owner):
    oid = await prepare()
    expected = await propose()
    await pay(oid)
    with pytest.raises(ServiceError, match="admin_activation_changed"):
        await commit(expected=expected)
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled
        assert (await db.get(StarCharge, "charge")).state == "paid"


async def test_enable_checks_version_and_required_provider(owner):
    with pytest.raises(ServiceError, match="provider_config"):
        await propose(True, "text_translation")
    async with sessions.begin() as db:
        (await db.get(Service, "images_to_pdf")).version = "old"
    with pytest.raises(ServiceError, match="service_changed"):
        await propose(True, "images_to_pdf")


async def test_enable_in_stars_mode_requires_owner_price(stars, owner):
    with pytest.raises(ServiceError, match="admin_missing_stars_price"):
        await propose(True, "images_to_pdf")


async def test_order_bound_refuses_without_mutation(owner, monkeypatch):
    await fund()
    await submit(1, "echo", {"text": "literal"}, 100, "bound")
    monkeypatch.setattr(activation, "MAX_ORDERS", 0)
    with pytest.raises(ServiceError, match="admin_activation_limit"):
        await propose()
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0


async def test_charge_bound_refuses_without_mutation(stars, owner, monkeypatch):
    oid = await prepare()
    await pay(oid)
    monkeypatch.setattr(activation, "MAX_CHARGES", 0)
    with pytest.raises(ServiceError, match="admin_activation_limit"):
        await propose()
    async with sessions() as db:
        assert (await db.get(Service, "echo")).enabled
        assert (await db.get(StarCharge, "charge")).state == "paid"
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0


async def test_router_review_confirm_cancel_history_and_customer_state(owner):
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    await state.set_state("support")
    await state.set_data({"key": "draft", "inputs": {"text": "preserve"}})
    try:
        await app.message("/admin")
        await app.callback("admin:inspect:echo")
        assert any(
            button.callback_data == "admin:activation:echo:0"
            for line in app.transport.messages[-1].reply_markup.inline_keyboard
            for button in line
        )
        await app.callback("admin:activation:echo:0")
        assert tr("admin_activation_disable_warning") in app.transport.messages[-1].text
        confirmation = app.transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
        async with sessions() as db:
            assert (await db.get(Service, "echo")).enabled
        await app.callback("admin:cancel")
        await app.callback(confirmation)
        async with sessions() as db:
            assert (await db.get(Service, "echo")).enabled
        await app.callback("admin:activation:echo:0")
        confirmation = app.transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
        await app.callback(confirmation)
        assert app.transport.messages[-1].text == tr("admin_activation_disabled")
        await app.callback(confirmation)
        async with sessions() as db:
            assert not (await db.get(Service, "echo")).enabled
            assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 1
        await app.callback("admin:activation_history")
        assert "echo" in app.transport.messages[-1].text
        assert (await state.get_data())["key"] == "draft"
        assert (await state.get_data())["inputs"] == {"text": "preserve"}
        assert await state.get_state() == "support"
    finally:
        await app.close()


@pytest.mark.parametrize("reason", ["expiry", "revoked", "foreign"])
async def test_router_rejects_expired_revoked_or_foreign_confirmations(owner, reason):
    from aiogram.types import User

    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    try:
        await app.message("/admin")
        await app.callback("admin:activation:echo:0")
        confirmation = app.transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
        if reason == "expiry":
            pending = (await state.get_data())["admin_activation"]
            pending["expires"] = 0
            await state.update_data(admin_activation=pending)
        elif reason == "revoked":
            config().admin_ids = []
        else:
            app.actor = User(id=8, is_bot=False, first_name="Other")
        await app.callback(confirmation)
        async with sessions() as db:
            assert (await db.get(Service, "echo")).enabled
            assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0
    finally:
        await app.close()
