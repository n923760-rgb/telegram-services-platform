import pytest
from sqlalchemy import func, select

from app.bot.followups import available_followups
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import CostHold, Order, Service, Setting, StarCharge
from app.core.settings import config
from app.core.users import set_language
from app.services.registry import registry
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix
from tests.test_foundation import fund
from tests.test_navigation import flow as flow
from tests.test_result_followups import completed as completed


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("paused", [False, True])
async def test_required_ai_selection_does_not_overwrite_draft_or_reserve(
    flow, monkeypatch, lang, paused
):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    monkeypatch.setattr(config(), "ai_enabled", paused)
    required = [
        slug
        for slug, plugin in registry.types.items()
        if plugin.requires_ai and registry.customer_visible(slug)
    ]
    async with sessions.begin() as db:
        for slug in required:
            (await db.get(Service, slug)).enabled = True
        if paused:
            db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    for slug in required:
        await callback("service:" + slug)
        assert transport.messages[-1].text == tr("service_ai_unavailable", lang)
        assert await state.get_data() == saved and await state.get_state() == "collect"
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_required_ai_intake_starts_normally_when_resumed(flow, monkeypatch):
    transport, message, callback, state = flow
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    async with sessions.begin() as db:
        (await db.get(Service, "cv_formatting")).enabled = True
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": False}))
    await message("/start")
    await callback("service:cv_formatting")
    assert (await state.get_data())["slug"] == "cv_formatting"
    assert await state.get_state() == "collect"
    assert tr("service_ai_unavailable") != transport.messages[-1].text


async def test_paused_direct_pdf_journey_still_submits_without_provider(flow, monkeypatch):
    transport, message, callback, state = flow
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    async with sessions.begin() as db:
        (await db.get(Service, "text_to_pdf")).enabled = True
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    await message("/start")
    await callback("service:text_to_pdf")
    await message("Literal 00123")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "skip:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.status == "queued" and order.inputs["mode"] == "direct"
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert (await balance(db, 1)).reserved == order.price_halala


async def test_stale_translation_followup_during_pause_preserves_source_and_empty_draft(
    flow, completed
):
    transport, message, callback, state = flow
    oid, *_ = completed
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
        original = (await db.get(Order, oid)).result
    assert not await available_followups(1, oid)
    await message("/start")
    await callback(f"follow:{oid.hex}:0")
    assert not (await state.get_data()).get("key")
    async with sessions() as db:
        assert (await db.get(Order, oid)).result == original
        assert await db.scalar(select(func.count(Order.id))) == 1


@pytest.mark.parametrize("stars", [False, True])
async def test_pause_after_form_completion_blocks_stale_confirmation_before_payment(
    flow, monkeypatch, stars
):
    transport, message, callback, state = flow
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    monkeypatch.setattr(config(), "stars_enabled", stars)
    monkeypatch.setattr(config(), "stars_terms_ar", "شروط اختبار")
    monkeypatch.setattr(config(), "stars_terms_en", "Test terms")
    async with sessions.begin() as db:
        service = await db.get(Service, "text_translation")
        service.enabled = True
        service.price_stars = 10
    await message("/start")
    await callback("service:text_translation")
    await message("Source text")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    confirmation = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    saved = await state.get_data()
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    await callback(confirmation)
    assert transport.messages[-1].text == tr("provider_config")
    assert await state.get_data() == saved
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_paused_resume_keeps_saved_required_ai_input_and_state(flow, monkeypatch):
    transport, message, callback, state = flow
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    async with sessions.begin() as db:
        (await db.get(Service, "text_translation")).enabled = True
    await message("/start")
    await callback("service:text_translation")
    await message("Saved source 00123")
    saved = await state.get_data()
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    for action in ("button", "command"):
        if action == "button":
            await callback("draft:resume")
        else:
            await message("/resume")
        assert transport.messages[-1].text == tr("service_ai_unavailable")
        assert await state.get_data() == saved and await state.get_state() == "collect"
    async with sessions.begin() as db:
        (await db.get(Setting, "PROVIDER_PAUSED")).value = {"value": False}
    await callback("draft:resume")
    assert transport.messages[-1].text.endswith(tr("text_translation_language"))
    assert (await state.get_data())["inputs"] == saved["inputs"]
