import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service
from app.core.settings import config
from app.core.users import set_language
from app.wallet.ledger import balance
from tests.test_foundation import fund
from tests.test_navigation import flow as flow


def controls(transport):
    return [b for row in transport.messages[-1].reply_markup.inline_keyboard for b in row]


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_all_services_grouped_without_root_service_buttons(flow, lang):
    transport, message, callback, _ = flow
    await set_language(1, lang)
    async with sessions.begin() as db:
        for service in (await db.scalars(select(Service))).all():
            service.enabled = True
    await message("/services")
    categories = [
        b.callback_data for b in controls(transport) if b.callback_data.startswith("catalog:")
    ]
    assert len(categories) == 7 and not any(
        b.callback_data.startswith("service:") for b in controls(transport)
    )
    await callback("catalog:data:0")
    assert [
        b.callback_data for b in controls(transport) if b.callback_data.startswith("service:")
    ] == ["service:csv_review", "service:pdf_tables_excel"]
    assert tr("catalog_data_description", lang) in transport.messages[-1].text
    await callback("menu:services")
    assert [
        b.callback_data for b in controls(transport) if b.callback_data.startswith("catalog:")
    ] == categories


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_browsing_keeps_draft_inputs_and_does_not_reserve(flow, lang):
    transport, message, callback, state = flow
    await fund()
    await set_language(1, lang)
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).enabled = True
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    await message("/services")
    await callback("catalog:data:0")
    await callback("catalog:data:999999")
    await callback("menu:services")
    assert await state.get_data() == saved and await state.get_state() == "collect"
    assert any(b.callback_data == "draft:resume" for b in controls(transport))
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_stale_disabled_category_has_only_safe_navigation(flow, lang):
    transport, message, callback, _ = flow
    await set_language(1, lang)
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).enabled = True
    await message("/services")
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).enabled = False
    await callback("catalog:data:0")
    assert transport.messages[-1].text == tr("catalog_empty", lang)
    assert not any(b.callback_data.startswith("service:") for b in controls(transport))
    assert any(b.callback_data == "menu:services" for b in controls(transport))


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_stars_availability_filter_still_applies_to_categories(flow, monkeypatch, lang):
    transport, message, callback, _ = flow
    await set_language(1, lang)
    monkeypatch.setattr(config(), "stars_enabled", True)
    async with sessions.begin() as db:
        echo = await db.get(Service, "echo")
        echo.enabled = False
        csv = await db.get(Service, "csv_review")
        csv.enabled, csv.price_stars = True, None
    await message("/services")
    assert transport.messages[-1].text == tr("no_services", lang)
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).price_stars = 5
    await message("/services")
    assert any(b.callback_data == "catalog:data:0" for b in controls(transport))
    await callback("catalog:data:0")
    assert any(b.callback_data == "service:csv_review" for b in controls(transport))


@pytest.mark.parametrize("data", ["catalog:unknown:0", "catalog:data:-1", "catalog:data:1000000"])
async def test_malformed_category_does_not_change_draft_or_create_orders(flow, data):
    _, message, callback, state = flow
    await message("/start")
    await callback("service:echo")
    saved = await state.get_data()
    await callback(data)
    assert await state.get_data() == saved and await state.get_state() == "collect"
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0


async def test_next_and_previous_dispatcher_pages_use_current_services(flow, monkeypatch):
    from app.bot import catalog

    transport, message, callback, _ = flow
    monkeypatch.setattr(catalog, "SERVICE_PAGE_SIZE", 1)
    async with sessions.begin() as db:
        for slug in ("csv_review", "pdf_tables_excel"):
            (await db.get(Service, slug)).enabled = True
    await message("/services")
    await callback("catalog:data:0")
    assert [
        b.callback_data for b in controls(transport) if b.callback_data.startswith("service:")
    ] == ["service:csv_review"]
    assert any(b.callback_data == "catalog:data:1" for b in controls(transport))
    await callback("catalog:data:1")
    assert [
        b.callback_data for b in controls(transport) if b.callback_data.startswith("service:")
    ] == ["service:pdf_tables_excel"]
    assert any(b.callback_data == "catalog:data:0" for b in controls(transport))
    await callback("catalog:data:0")
    assert any(b.callback_data == "service:csv_review" for b in controls(transport))
