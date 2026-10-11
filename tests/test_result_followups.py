import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from aiogram import Bot
from sqlalchemy import func, select

from app.bot.followups import available_followups
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Job, Order, Service
from app.core.settings import config
from app.providers.delivery import TelegramDelivery
from app.services.base import Result
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_bounded_fixes import button_by_prefix
from tests.test_draft_recovery import SimulatedSendFailure
from tests.test_foundation import job_for
from tests.test_navigation import flow as flow
from tests.test_ocr_translation_flow import create_order, extracted
from tests.test_ocr_translation_quality import GOOD, SOURCE
from tests.test_real_services import setup


@pytest.fixture
async def completed(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", [extracted(SOURCE)], tmp_path, monkeypatch
    )
    oid = await create_order(store, price)
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions.begin() as db:
        (await db.get(Service, "text_translation")).enabled = True
    return oid, store, provider, delivery, ctx, price


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_original_then_independent_translation_intake_and_single_capture(
    flow, completed, lang
):
    from app.core.users import set_language

    transport, message, callback, state = flow
    oid, _, provider, delivery, ctx, price = completed
    await set_language(1, lang)
    await message("/start")
    await callback(f"follow:{oid.hex}:0")
    assert transport.messages[-1].text.endswith(tr("text_translation_language", lang))
    assert (await state.get_data())["inputs"] == {"text": SOURCE}
    # Choosing the language then style follows the ordinary independent intake.
    data = await state.get_data()
    await callback(f"choice:{data['key']}:1:1")
    assert transport.messages[-1].text.endswith(tr("translation_style", lang))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert (await balance(db, 1)).reserved == 0
        assert (await db.get(Order, oid)).result["text"] == SOURCE
    assert tr("confirm_price", lang, amount="3.00") in transport.messages[-1].text
    confirm = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    await callback(confirm)
    await callback(confirm)
    async with sessions() as db:
        new_order = await db.scalar(select(Order).where(Order.id != oid))
        assert new_order.service_slug == "text_translation"
        assert new_order.inputs == {"text": SOURCE, "language": "en", "style": "formal"}
        target_id = new_order.id
        assert await db.scalar(select(func.count(Order.id))) == 2
    provider.responses.append(json.dumps({"segments": [{"id": 1, "text": GOOD}]}))
    await execute_job(ctx, str(await job_for(target_id)))
    await execute_job(ctx, str(await job_for(target_id)))
    assert provider.calls == 2 and [result.text for result in delivery.results] == [SOURCE, GOOD]
    async with sessions() as db:
        assert (await db.get(Order, oid)).result["text"] == SOURCE
        assert (await db.get(Order, target_id)).status == "completed"
        assert (await balance(db, 1)).available == 1000 - price - 300


@pytest.mark.parametrize("slug", ["image_to_text", "local_ocr"])
@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_delivery_places_optional_button_after_original_text(flow, completed, slug, lang):
    from app.core.users import set_language

    transport, message, callback, state = flow
    oid, store, _, _, _, _ = completed
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.service_slug, order.service_version = slug, registry.types[slug].version
        order.status = "delivering"
    await set_language(1, lang)
    await message("/start")
    adapter = TelegramDelivery(Bot("123456:TEST_TOKEN_ONLY", session=transport), store)
    await adapter.send(1, oid, Result(text=SOURCE))
    assert transport.messages[-2].text == SOURCE
    assert transport.messages[-1].text == tr("result_followups", lang)
    rows = transport.messages[-1].reply_markup.inline_keyboard
    assert [len(row) for row in rows] == [1, 1, 1]
    assert [(row[0].text, row[0].callback_data) for row in rows] == [
        (tr("home", lang), "menu:home"),
        (tr("result_another_service", lang), "menu:services"),
        (tr("translate_result", lang), f"follow:{oid.hex}:0"),
    ]
    assert button_by_prefix(transport.messages[-1].reply_markup, "follow:") == f"follow:{oid.hex}:0"
    assert len(f"follow:{oid.hex}:0".encode()) <= 64
    for navigation in ("menu:home", "menu:services"):
        await callback(navigation)
        assert await state.get_state() is None
        assert "inputs" not in await state.get_data()
        async with sessions() as db:
            assert await db.scalar(select(func.count(Order.id))) == 1
            assert (await balance(db, 1)).reserved == 0
            assert (await db.get(Order, oid)).result["text"] == SOURCE


@pytest.mark.parametrize(
    "change",
    [
        "owner",
        "status",
        "expired",
        "purged",
        "old_source",
        "disabled",
        "old_target",
        "schema",
        "ai",
        "long",
        "lines",
        "control",
        "empty",
        "stars_unpriced",
        "missing",
    ],
)
async def test_unavailable_results_and_changed_targets_never_start_draft(
    flow, completed, monkeypatch, change
):
    transport, message, callback, state = flow
    oid, _, provider, _, _, _ = completed
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        target = await db.get(Service, "text_translation")
        if change == "owner":
            from app.orders.engine import register

            await register(2)
            order.user_id = 2
        elif change == "status":
            order.status = "delivering"
        elif change == "expired":
            order.updated_at = datetime.now(UTC) - timedelta(hours=config().file_ttl_hours + 1)
        elif change == "purged":
            order.result = None
        elif change == "old_source":
            order.service_version = "2"
        elif change == "disabled":
            target.enabled = False
        elif change == "old_target":
            target.version = "stale"
        elif change == "schema":
            target.input_schema = {"fields": []}
        elif change == "ai":
            monkeypatch.setattr(config(), "ai_enabled", False)
        elif change in {"long", "lines", "control", "empty"}:
            order.result = Result(
                text={
                    "long": "x" * 12001,
                    "lines": "line\n" * 81,
                    "control": "bad\x01",
                    "empty": " ",
                }[change]
            ).model_dump(mode="json")
        elif change == "stars_unpriced":
            monkeypatch.setattr(config(), "stars_enabled", True)
        elif change == "missing":
            oid = uuid4()
    await message("/start")
    saved = await state.get_data()
    await callback(f"follow:{oid.hex}:0")
    assert await state.get_data() == saved
    assert transport.callback_answers[-1].show_alert
    assert not await available_followups(1, oid)
    assert provider.calls == 1
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert await db.scalar(select(func.count(Job.id))) == 1
        assert (await balance(db, 1)).reserved == 0


async def test_existing_draft_and_repeated_click_are_preserved(flow, completed):
    transport, message, callback, state = flow
    oid, *_ = completed
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    await callback(f"follow:{oid.hex}:0")
    assert await state.get_data() == saved
    assert transport.messages[-1].text == tr("followup_draft_exists")
    await message("/cancel")
    await callback(f"follow:{oid.hex}:0")
    saved = await state.get_data()
    await callback(f"follow:{oid.hex}:0")
    assert await state.get_data() == saved
    await message("/cancel")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert (await balance(db, 1)).reserved == 0


async def test_failed_followup_prompt_recovers_without_losing_source(flow, completed):
    transport, message, callback, state = flow
    oid, *_ = completed
    await message("/start")
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await callback(f"follow:{oid.hex}:0")
    saved = await state.get_data()
    assert saved["pending_prompt"] and saved["inputs"] == {"text": SOURCE}
    await callback(f"follow:{oid.hex}:0")
    recovered = await state.get_data()
    assert not recovered["pending_prompt"] and recovered["key"] == saved["key"]
    assert recovered["index"] == 1 and recovered["inputs"] == {"text": SOURCE}
    assert transport.messages[-1].text.endswith(tr("text_translation_language"))


async def test_live_target_price_is_used_and_rechecked_before_purchase(flow, completed):
    transport, message, callback, state = flow
    oid, *_ = completed
    async with sessions.begin() as db:
        (await db.get(Service, "text_translation")).price_halala = 450
    await message("/start")
    await callback(f"follow:{oid.hex}:0")
    assert (await state.get_data())["price"] == 450
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    async with sessions.begin() as db:
        (await db.get(Service, "text_translation")).enabled = False
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert (await balance(db, 1)).reserved == 0


async def test_blank_lines_and_original_source_are_preserved(flow, completed):
    _, message, callback, state = flow
    oid, *_ = completed
    text = "  " + SOURCE + "\n\nEnglish 00123  "
    async with sessions.begin() as db:
        (await db.get(Order, oid)).result = Result(text=text).model_dump(mode="json")
    await message("/start")
    await callback(f"follow:{oid.hex}:0")
    assert (await state.get_data())["inputs"] == {"text": text}
