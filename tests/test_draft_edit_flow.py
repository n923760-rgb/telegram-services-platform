"""Actual dispatcher and PostgreSQL admission after generic draft editing."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order
from app.core.users import set_language
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix
from tests.test_foundation import fund
from tests.test_navigation import flow as flow
from tests.test_stars import stars as stars


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_edit_creates_no_order_or_reservation_and_only_new_confirm_submits(flow, lang):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await message("/services")
    await callback("service:echo")
    await message("Original 00123")
    old_key = (await state.get_data())["key"]
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "edit:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "editfield:"))
    await message("Revised 00123")
    new_key = (await state.get_data())["key"]
    assert new_key != old_key and await state.get_state() == "confirm"
    await callback(f"confirm:{old_key}")
    assert transport.messages[-1].text == tr("stale_button", lang)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Order)) == 0
        assert (await balance(db, 1)).reserved == 0
    await callback(f"confirm:{new_key}")
    await callback(f"confirm:{new_key}")
    async with sessions() as db:
        orders = list(await db.scalars(select(Order)))
        assert len(orders) == 1
        assert orders[0].inputs == {"text": "Revised 00123"}
        assert (await balance(db, 1)).reserved == 100


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_abort_edit_restores_original_for_one_purchase(flow, lang):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await message("/services")
    await callback("service:echo")
    await message("Original 00123")
    old_key = (await state.get_data())["key"]
    await callback(f"editfield:{old_key}:0")
    editing_key = (await state.get_data())["key"]
    await callback(f"editabort:{editing_key}")
    restored = await state.get_data()
    assert restored["inputs"] == {"text": "Original 00123"}
    assert restored["key"] not in {old_key, editing_key}
    await callback(f"confirm:{restored['key']}")
    async with sessions() as db:
        orders = list(await db.scalars(select(Order)))
        assert len(orders) == 1 and orders[0].inputs == restored["inputs"]
        assert (await balance(db, 1)).reserved == 100


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_durable_order_blocks_edit_after_lost_fsm_clear(flow, lang):
    from app.orders.engine import submit

    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await message("/services")
    await callback("service:echo")
    await message("Already accepted 00123")
    original = await state.get_data()
    # Reproduce the crash window: durable admission succeeded but FSM still shows
    # confirmation. This applies to any accepted status, not merely an FSM flag.
    await submit(
        1, "echo", original["inputs"], original["price"], original["key"], original["version"]
    )
    await callback(f"edit:{original['key']}")
    assert await state.get_data() == original
    await callback(f"editfield:{original['key']}:0")
    assert await state.get_data() == original
    async with sessions() as db:
        orders = list(await db.scalars(select(Order)))
        assert len(orders) == 1 and orders[0].inputs == original["inputs"]
        assert (await balance(db, 1)).reserved == 100


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_failed_stars_invoice_blocks_edits_and_retries_same_order(
    flow, stars, monkeypatch, lang
):
    from app.core.models import Job, StarCheckout
    from app.ops.admin import set_service

    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await set_service("echo", stars=20, enabled=True)
    await message("/services")
    await callback("service:echo")
    await message("Original invoice 00123")
    original = await state.get_data()
    failed_invoice = AsyncMock(side_effect=RuntimeError("lost invoice send"))
    monkeypatch.setattr("app.bot.payments.invoice", failed_invoice)
    with pytest.raises(RuntimeError, match="lost invoice send"):
        await callback(f"confirm:{original['key']}")
    assert await state.get_state() == "confirm" and await state.get_data() == original
    await callback(f"edit:{original['key']}")
    await callback(f"editfield:{original['key']}:0")
    assert await state.get_data() == original
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.status == "awaiting_payment" and order.inputs == original["inputs"]
        assert await db.scalar(select(func.count()).select_from(Order)) == 1
        assert await db.scalar(select(func.count()).select_from(StarCheckout)) == 1
        assert await db.scalar(select(func.count()).select_from(Job)) == 0
        assert (await balance(db, 1)).reserved == 0
        order_id = order.id
    retried_invoice = AsyncMock()
    monkeypatch.setattr("app.bot.payments.invoice", retried_invoice)
    await callback(f"confirm:{original['key']}")
    assert await state.get_state() is None
    assert retried_invoice.await_args.args[1] == order_id
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Order)) == 1
        assert await db.scalar(select(func.count()).select_from(StarCheckout)) == 1
        assert (await balance(db, 1)).reserved == 0
