import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Job, Order, Service, StarCharge
from app.core.settings import config
from app.core.users import set_language
from app.orders.engine import submit
from app.payments.stars import payload, pre_checkout
from app.services.base import ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for
from tests.test_navigation import flow as flow
from tests.test_stars import pay, prepare
from tests.test_stars import stars as stars


@pytest.fixture
def private(database, monkeypatch):
    # Restore production policy after the shared public financial-test plugin setup.
    monkeypatch.setattr(registry.types["echo"], "admin_only", True)
    monkeypatch.setattr(config(), "admin_ids", [7])


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_customer_old_menu_and_direct_selection_cannot_replace_draft(flow, private, lang):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await state.set_state("support")
    await state.set_data({"key": "saved", "inputs": {"text": "original"}})
    await message("/services")
    assert transport.messages[-1].text == tr("no_services", lang)
    saved = await state.get_data()
    await callback("catalog:other:0")
    assert transport.messages[-1].text == tr("catalog_empty", lang)
    await callback("service:echo")
    assert transport.messages[-1].text == tr("unavailable", lang)
    assert await state.get_data() == saved
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


@pytest.mark.parametrize("allowed", [True, False])
async def test_submission_checks_role_before_new_reservation(private, allowed):
    user_id = 7 if allowed else 1
    await fund(user_id)
    if allowed:
        oid = await submit(user_id, "echo", {"text": "test"}, 100, "private")
        delivery = Delivery()
        await execute_job({"delivery": delivery}, str(await job_for(oid)))
        assert delivery.results[0].text == "test"
    else:
        with pytest.raises(ServiceError, match="unavailable"):
            await submit(user_id, "echo", {"text": "test"}, 100, "private")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == int(allowed)
        funds = await balance(db, user_id)
        assert (funds.available, funds.reserved) == (900 if allowed else 1000, 0)


async def test_admin_menu_visible_and_revoked_confirm_creates_no_order(flow, private, monkeypatch):
    transport, message, callback, state = flow
    monkeypatch.setattr(config(), "admin_ids", [1])
    await fund()
    await message("/services")
    assert any(
        b.callback_data == "catalog:other:0"
        for line in transport.messages[-1].reply_markup.inline_keyboard
        for b in line
    )
    await callback("catalog:other:0")
    await callback("service:echo")
    await message("internal test")
    confirm = next(
        b.callback_data
        for line in transport.messages[-1].reply_markup.inline_keyboard
        for b in line
        if b.callback_data.startswith("confirm:")
    )
    monkeypatch.setattr(config(), "admin_ids", [])
    await callback(confirm)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_private_policy_is_generic_for_future_services(private, monkeypatch):
    monkeypatch.setattr(registry.types["text_editing"], "admin_only", True)
    await fund()
    async with sessions.begin() as db:
        (await db.get(Service, "text_editing")).enabled = True
    with pytest.raises(ServiceError, match="unavailable"):
        await submit(1, "text_editing", {"text": "source", "mode": "proofread"}, 300, "generic")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Job.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_revoked_admin_unpaid_checkout_is_rejected(private, stars, monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [1])
    oid = await prepare()
    monkeypatch.setattr(config(), "admin_ids", [])
    with pytest.raises(ServiceError, match="payment_invalid"):
        await pre_checkout(1, payload(oid), "XTR", 20, "revoked-query")
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "awaiting_payment"
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0


async def test_already_paid_order_survives_role_revocation(private, stars, monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [1])
    oid = await prepare()
    await pay(oid, charge="private-paid")
    monkeypatch.setattr(config(), "admin_ids", [])
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await db.get(StarCharge, "private-paid")).state == "paid"
