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
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    await message("Literal 00123")
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


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize(
    "slug,index,inputs,selected",
    [
        ("text_to_office", 0, {}, 1),
        ("text_to_office", 1, {"target": "word"}, 1),
        ("text_to_word_pdf", 1, {"output_format": "pdf"}, 1),
        ("text_to_pdf", 0, {}, 1),
        ("pdf_tables_excel", 0, {}, 2),
    ],
)
async def test_mixed_choice_pause_recheck_preserves_draft_without_admission(
    flow, monkeypatch, lang, slug, index, inputs, selected
):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    monkeypatch.setattr(config(), "ai_enabled", True)
    async with sessions.begin() as db:
        (await db.get(Service, slug)).enabled = True
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": False}))
    await message("/start")
    await callback("service:" + slug)
    data = await state.get_data()
    # Resume a real pre-upgrade choice schema rather than a new automatic intake.
    if slug != "pdf_tables_excel":
        schema = registry.types[slug].input_schema.model_copy(deep=True)
        for field in schema.fields:
            field.legacy_only = False
        monkeypatch.setattr(registry.types[slug], "input_schema", schema)
        data["schema"] = schema.model_dump()
    data.update(index=index, inputs=inputs, pending_prompt=False)
    await state.set_data(data)
    await callback("draft:resume")
    field = registry.types[slug].input_schema.conversation()[index]
    assert tr("intake_direct_only", lang) not in transport.messages[-1].text
    choice = f"choice:{data['key']}:{index}:{selected}"
    saved = await state.get_data()
    async with sessions.begin() as db:
        (await db.get(Setting, "PROVIDER_PAUSED")).value = {"value": True}
    # The old enabled button is checked again against current pause status.
    await callback(choice)
    assert transport.callback_answers[-1].text == tr("intake_option_unavailable", lang)
    assert transport.callback_answers[-1].show_alert
    assert await state.get_data() == saved and await state.get_state() == "collect"
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert (await balance(db, 1)).reserved == 0
    await callback("draft:resume")
    assert tr("intake_direct_only", lang) in transport.messages[-1].text
    buttons = [b for row in transport.messages[-1].reply_markup.inline_keyboard for b in row]
    assert buttons[selected].text == tr(
        "intake_choice_unavailable", lang, choice=tr(field.choice_keys[selected], lang)
    )
    async with sessions.begin() as db:
        (await db.get(Setting, "PROVIDER_PAUSED")).value = {"value": False}
    await callback(choice)
    current = await state.get_data()
    assert current["inputs"] == inputs | {field.name: field.choices[selected]}
    assert current["key"] == saved["key"] and current["price"] == saved["price"]


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("slug,blocked", [("text_to_pdf", 1), ("pdf_tables_excel", 2)])
@pytest.mark.parametrize("paused", [False, True])
async def test_mode_is_first_and_unavailable_choice_never_requests_source(
    flow, monkeypatch, lang, slug, blocked, paused
):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    monkeypatch.setattr(config(), "ai_enabled", paused)
    async with sessions.begin() as db:
        (await db.get(Service, slug)).enabled = True
        if paused:
            db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    await message("/start")
    await callback("service:" + slug)
    if slug == "text_to_pdf":
        schema = registry.types[slug].input_schema.model_copy(deep=True)
        for field in schema.fields:
            field.legacy_only = False
        monkeypatch.setattr(registry.types[slug], "input_schema", schema)
        await state.update_data(schema=schema.model_dump())
        await callback("draft:resume")
    saved = await state.get_data()
    fields = registry.types[slug].input_schema.conversation()
    assert saved["index"] == 0 and saved["inputs"] == {} and fields[0].name == "mode"
    assert transport.messages[-1].text.endswith(tr(fields[0].prompt_key, lang))
    await message("Premature source 00123")
    assert transport.messages[-1].text == tr("choose_option", lang)
    assert await state.get_data() == saved
    await callback(f"choice:{saved['key']}:0:{blocked}")
    assert transport.callback_answers[-1].text == tr("intake_option_unavailable", lang)
    assert await state.get_data() == saved
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert (await balance(db, 1)).reserved == 0
    await callback(f"choice:{saved['key']}:0:0")
    assert transport.messages[-1].text.endswith(tr(fields[1].prompt_key, lang))
    assert (await state.get_data())["inputs"] == {"mode": "direct"}


@pytest.mark.parametrize("slug", ["text_to_pdf", "pdf_tables_excel"])
async def test_saved_v4_confirmation_keeps_draft_and_rejects_before_reservation(flow, slug):
    transport, message, callback, state = flow
    await fund()
    async with sessions.begin() as db:
        (await db.get(Service, slug)).enabled = True
    await message("/start")
    await callback("service:" + slug)
    data = await state.get_data()
    data["schema"]["fields"][:2] = reversed(data["schema"]["fields"][:2])
    data.update(
        version="4",
        index=len(data["schema"]["fields"]),
        inputs={"mode": "direct", "text": "Saved 00123"}
        if slug == "text_to_pdf"
        else {"mode": "direct", "pdf": "1/" + "a" * 32 + "/source.pdf", "language": "ar"},
    )
    await state.set_data(data)
    await state.set_state("confirm")
    await callback("draft:resume")
    saved = await state.get_data()
    await callback(f"confirm:{saved['key']}")
    assert transport.messages[-1].text == tr("service_changed")
    assert await state.get_data() == saved and await state.get_state() == "confirm"
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0
        assert (await balance(db, 1)).reserved == 0
