"""Real dispatcher journeys: navigation never becomes input or loses a saved draft."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import func, select

from app.bot.main import create_dispatcher
from app.bot.navigation import status_label
from app.bot.ui import HOME_ITEMS
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service, SupportTicket
from app.core.settings import config
from app.core.users import set_language
from app.orders.engine import register, submit
from app.orders.state import ALLOWED
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix, feeders
from tests.test_draft_recovery import FlakyRecorder, SimulatedSendFailure
from tests.test_foundation import fund


@pytest.fixture
async def flow():
    from aiogram.types import User

    transport = FlakyRecorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = User(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    state = dp.fsm.get_context(bot=bot, chat_id=user.id, user_id=user.id)
    yield transport, message, callback, state
    await dp.storage.close()
    await bot.session.close()


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_home_has_persistent_two_column_keyboard(flow, lang):
    transport, message, _, _ = flow
    await set_language(1, lang)
    await message("/start")
    keyboard = transport.sent_methods[-1].reply_markup
    assert keyboard.is_persistent and keyboard.resize_keyboard
    assert [len(row) for row in keyboard.keyboard] == [2, 2, 2]
    assert [button.text for row in keyboard.keyboard for button in row] == [
        tr(key, lang) for key in HOME_ITEMS
    ]


@pytest.mark.parametrize("target", ["services", "orders", "balance", "help", "language"])
@pytest.mark.parametrize("via_callback", [False, True])
async def test_navigation_preserves_draft_and_does_not_become_customer_text(
    flow, target, via_callback
):
    transport, message, callback, state = flow
    await fund()
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    if via_callback:
        await callback(f"menu:{target}")
    else:
        await message(tr(target))
    assert await state.get_data() == saved
    assert await state.get_state() == "collect"
    assert button_by_prefix(transport.messages[-1].reply_markup, "draft:resume")
    await callback("draft:resume")
    await message("Actual customer content")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    async with sessions() as db:
        orders = list(await db.scalars(select(Order)))
        assert len(orders) == 1
        assert orders[0].inputs == {"text": "Actual customer content"}
        assert (await balance(db, 1)).reserved == 100


async def test_start_and_menu_preserve_confirmed_draft_and_scoped_cancel(flow):
    transport, message, callback, state = flow
    await fund()
    await message("/start")
    await callback("service:echo")
    await message("Saved content")
    saved = await state.get_data()
    for navigation in ("/start", "/menu"):
        await message(navigation)
        assert await state.get_data() == saved
        assert await state.get_state() == "confirm"
        assert transport.messages[-1].text == tr("draft_saved")
    await callback("draft:resume")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "cancel:"))
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


async def test_old_language_keyboard_is_reserved_navigation(flow):
    _, message, callback, state = flow
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    await callback("lang:en")
    await message(tr("orders", "ar"))
    assert await state.get_data() == saved
    assert await state.get_state() == "collect"


async def test_language_switch_resends_current_question_without_losing_inputs(flow):
    transport, message, callback, state = flow
    async with sessions.begin() as db:
        (await db.get(Service, "text_to_office")).enabled = True
    await message("/start")
    await callback("service:text_to_office")
    await message("محتوى العميل")
    saved = await state.get_data()
    await callback("lang:en")
    assert await state.get_data() == saved
    assert transport.messages[-1].text.endswith(tr("office_target", "en"))
    assert "Step 2" in transport.messages[-1].text
    assert transport.sent_methods[-2].reply_markup.keyboard[0][0].text == tr("services", "en")


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_direct_document_intake_is_explicit_and_preserves_customer_text(flow, lang, slug):
    from app.ops.admin import set_service

    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await set_service(slug, enabled=True)
    await message("/start")
    await callback(f"service:{slug}")
    text = (
        "بدون تعديل النص\n" if slug == "text_to_office" else ""
    ) + "  نص جاهز 00123\n\nEnglish & <tag>  "
    await message(text)
    if slug == "text_to_office":
        await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    if slug == "text_to_pdf":
        assert transport.messages[-1].text.endswith(tr("document_mode", lang))
        await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
        assert transport.messages[-1].text.endswith(tr("document_title", lang))
        await message("عنوان العميل")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    assert await state.get_state() is None
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs["text"] == text
        if slug == "text_to_pdf":
            assert order.inputs["mode"] == "direct" and order.inputs["title"] == "عنوان العميل"
        else:
            assert set(order.inputs) == {"text", "target"}
        assert order.service_version == ("5" if slug == "text_to_office" else "3")


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("slug", ["text_to_pdf"])
async def test_optional_title_rejects_multiline_then_skips_without_losing_body(flow, lang, slug):
    from app.ops.admin import set_service

    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    await set_service(slug, enabled=True)
    await message("/start")
    await callback(f"service:{slug}")
    text = "نص 00123\n\nEnglish 125.50"
    await message(text)
    if slug == "text_to_office":
        await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    choice = button_by_prefix(transport.messages[-1].reply_markup, "choice:")
    await callback(choice.rsplit(":", 1)[0] + (":1" if slug == "text_to_office" else ":0"))
    markup = transport.messages[-1].reply_markup
    skip = button_by_prefix(markup, "skip:")
    assert any(
        b.text == tr("document_no_title", lang) for row in markup.inline_keyboard for b in row
    )
    draft = await state.get_data()
    await message(text)
    assert transport.messages[-1].text == tr("input_single_line", lang)
    assert await state.get_data() == draft
    await callback(skip)
    assert await state.get_state() == "confirm"
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs["text"] == text and "title" not in order.inputs
        assert (await balance(db, 1)).reserved == order.price_halala


async def test_smart_word_mode_skips_title_and_rejects_disabled_provider(flow):
    from app.ops.admin import set_service

    transport, message, callback, state = flow
    await fund()
    await set_service("text_to_office", enabled=True)
    await message("/start")
    await callback("service:text_to_office")
    await message("نص العميل")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    assert await state.get_state() == "confirm"
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    assert transport.messages[-1].text == tr("provider_config")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_navigation_preserves_pending_prompt_recovery(flow):
    transport, message, callback, state = flow
    await message("/start")
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await callback("service:echo")
    assert (await state.get_data())["pending_prompt"]
    await message(tr("orders"))
    assert (await state.get_data())["pending_prompt"]
    await callback("draft:resume")
    assert not (await state.get_data())["pending_prompt"]
    assert (await state.get_data())["inputs"] == {}
    await message("one answer")
    assert (await state.get_data())["inputs"] == {"text": "one answer"}


@pytest.mark.parametrize("finish", ["send", "home", "resume"])
async def test_support_preserves_and_restores_intake_draft(flow, monkeypatch, finish):
    transport, message, callback, state = flow
    monkeypatch.setattr(config(), "admin_ids", [100])
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    await message(tr("support"))
    assert await state.get_state() == "support"
    if finish == "send":
        await message("Help with my draft")
        assert transport.copies
        assert transport.messages[-1].text == tr("support_sent")
    elif finish == "home":
        await callback("menu:home")
    else:
        await callback("draft:resume")
    assert await state.get_state() == "collect"
    assert await state.get_data() == saved
    await message("the actual content")
    assert (await state.get_data())["inputs"] == {"text": "the actual content"}


async def test_support_command_registers_new_user_and_can_exit(flow):
    _, message, _, state = flow
    await message("/support")
    async with sessions() as db:
        from app.core.models import User

        assert await db.get(User, 1) is not None
    assert await state.get_state() == "support"
    await message("/cancel")
    assert await state.get_state() is None


async def test_menu_labels_are_not_forwarded_as_support_content(flow, monkeypatch):
    transport, message, _, state = flow
    monkeypatch.setattr(config(), "admin_ids", [100])
    await message("/support")
    await message(tr("orders"))
    assert await state.get_state() is None
    assert transport.copies == []
    async with sessions() as db:
        assert await db.scalar(select(func.count(SupportTicket.id))) == 0


async def create_history(user_id, count):
    await register(user_id)
    orders = []
    async with sessions.begin() as db:
        for index in range(count):
            order = Order(
                user_id=user_id,
                service_slug="echo",
                price_halala=100,
                idempotency_key=f"history:{user_id}:{index}",
                input_hash="history",
                inputs={},
                status="completed",
                created_at=datetime(2026, 10, 7, 12, tzinfo=UTC) + timedelta(minutes=index),
            )
            db.add(order)
            await db.flush()
            orders.append(order.id)
    return orders


async def test_history_is_paginated_newest_first_and_excludes_other_users(flow):
    transport, message, callback, _ = flow
    owned = await create_history(1, 8)
    others = await create_history(2, 2)
    await message("/orders")
    markup = transport.messages[-1].reply_markup
    data = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert [value for value in data if value.startswith("order:")] == [
        f"order:{order_id}" for order_id in reversed(owned[2:])
    ]
    assert "orders:1" in data
    assert not any(f"order:{order_id}" in data for order_id in others)
    await callback("orders:1")
    markup = transport.messages[-1].reply_markup
    data = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert [value for value in data if value.startswith("order:")] == [
        f"order:{owned[1]}",
        f"order:{owned[0]}",
    ]
    assert "orders:0" in data and "orders:2" not in data


async def test_order_detail_owner_check_and_no_content_disclosure(flow):
    transport, message, callback, _ = flow
    owned = (await create_history(1, 1))[0]
    other = (await create_history(2, 1))[0]
    async with sessions.begin() as db:
        (await db.get(Order, owned)).inputs = {"text": "Private source text"}
    await message("/orders")
    await callback(f"order:{owned}")
    assert str(owned) in transport.messages[-1].text
    assert "2026-10-07 15:00" in transport.messages[-1].text
    assert "Private source text" not in transport.messages[-1].text
    count = len(transport.messages)
    for order_id in (other, uuid4()):
        await callback(f"order:{order_id}")
        assert transport.callback_answers[-1].text == tr("order_unavailable")
        assert transport.callback_answers[-1].show_alert
        assert len(transport.messages) == count


@pytest.mark.parametrize("data", ["orders:-1", "orders:1000", "orders:no", "orders:١", "order:bad"])
async def test_malformed_history_controls_are_answered_without_db_mutation(flow, data):
    transport, message, callback, _ = flow
    await message("/start")
    await callback(data)
    assert transport.callback_answers[-1].text == tr("invalid_request")
    assert transport.callback_answers[-1].show_alert
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_history_refresh_reads_current_state_without_financial_writes(flow, lang):
    transport, message, callback, _ = flow
    await fund()
    await set_language(1, lang)
    order_id = await submit(1, "echo", {"text": "content"}, 100, "real-order")
    await message("/orders")
    await callback(f"order:{order_id}")
    assert tr("status_queued", lang) in transport.messages[-1].text
    async with sessions.begin() as db:
        (await db.get(Order, order_id)).status = "processing"
    await callback(f"order:{order_id}")
    assert tr("status_processing", lang) in transport.messages[-1].text
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (900, 100)


async def test_waiting_order_can_be_cancelled_from_history_once(flow):
    transport, message, callback, _ = flow
    await fund()
    order_id = await submit(1, "echo", {"text": "content"}, 100, "awaiting")
    async with sessions.begin() as db:
        order = await db.get(Order, order_id)
        order.status = "waiting_confirmation"
        order.result = {"preview": "Please review", "continuation": {"accepted": True}}
    await message("/orders")
    await callback(f"order:{order_id}")
    assert "Please review" in transport.messages[-1].text
    reject = button_by_prefix(transport.messages[-1].reply_markup, "reject:")
    assert reject == f"reject:{order_id}"
    await callback(reject)
    await callback(reject)
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


async def test_all_order_states_have_localized_labels():
    for status in ALLOWED:
        for lang in ("ar", "en"):
            assert status_label(status, lang) != f"status_{status}"
    assert status_label("unexpected", "en") == tr("status_unknown", "en")


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_waiting_history_and_notification_show_complete_localized_preview(
    flow, tmp_path, lang
):
    from app.providers.storage import LocalStorage
    from app.workers.runner import deliver_confirmations
    from tests.test_real_services import Delivery

    transport, message, callback, _ = flow
    await fund()
    await set_language(1, lang)
    oid = await submit(1, "echo", {"text": "content"}, 100, "preview-language")
    previews = {
        "ar": "عربي " + "🙂" * 2700 + "آخر عمود",
        "en": "English " + "🙂" * 2700 + "LAST COLUMN",
    }
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status = "waiting_confirmation"
        order.result = {
            "preview": "Legacy English",
            "preview_localizations": previews,
            "continuation": {"accepted": True},
        }
    delivery = Delivery(LocalStorage(tmp_path))
    await deliver_confirmations({"delivery": delivery})
    assert delivery.confirmations[0][1] == previews[lang]
    await message("/orders")
    before = len(transport.messages)
    await callback(f"order:{oid}")
    messages = transport.messages[before:]
    assert previews[lang] in "".join(m.text for m in messages)
    assert all(len(m.text.encode("utf-16-le")) // 2 <= 3500 for m in messages)
    assert all(m.reply_markup is None for m in messages[:-1])
    data = [b.callback_data for row in messages[-1].reply_markup.inline_keyboard for b in row]
    assert f"approve:{oid}" in data and f"reject:{oid}" in data


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_service_buttons_show_name_and_price_only_at_confirmation(flow, lang):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    async with sessions.begin() as db:
        service = await db.get(Service, "echo")
        service.price_halala = 1234
        service.name_ar = "خدمة تجريبية PDF إلى Excel"
        service.name_en = "PDF to Excel demo"
    await message("/services")
    await callback("catalog:other:0")
    markup = transport.messages[-1].reply_markup
    control = next(
        b for row in markup.inline_keyboard for b in row if b.callback_data == "service:echo"
    )
    assert control.text == ("خدمة تجريبية PDF إلى Excel" if lang == "ar" else "PDF to Excel demo")
    assert "12.34" not in transport.messages[-1].text
    await callback(control.callback_data)
    await message("Customer content")
    review = transport.messages[-1].text
    assert tr("confirm_price", lang, amount="12.34") in review
    assert review.split("\n\n")[1] == tr("confirm_price", lang, amount="12.34").split("\n\n")[0]
    assert await state.get_state() == "confirm"
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Order)) == 0
