"""Presentation changes preserve registered identity, configuration and draft state."""

import pytest
from sqlalchemy import func, select

from app.bot.catalog import view
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service, StarPriceChange
from app.services.registry import registry
from tests.test_admin_prices import Conversation
from tests.test_admin_prices import owner as owner


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_renaming_sync_preserves_versions_prices_activation_and_history(lang):
    async with sessions.begin() as db:
        row = await db.get(Service, "text_editing")
        old_version, old_schema = row.version, row.input_schema
        row.name_ar, row.name_en = "اسم قديم", "Old name"
        row.enabled, row.price_halala, row.price_stars = True, 777, 31
    async with sessions.begin() as db:
        await registry.sync(db)
        row = await db.get(Service, "text_editing")
        assert row.name_ar == "تحرير النصوص" and row.name_en == "Text editing"
        assert row.version == old_version and row.input_schema == old_schema
        assert row.enabled and row.price_halala == 777 and row.price_stars == 31
        _, items = view([row], lang, category="text")
        assert items[0] == (tr("text_editing_name", lang), "service:text_editing")
        assert await db.scalar(select(func.count(StarPriceChange.id))) == 0


async def test_admin_pages_show_same_customer_labels_and_keep_draft(owner):
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    await state.set_state("collect")
    await state.set_data({"key": "draft", "inputs": {"text": "saved"}})
    try:
        await app.message("/admin")
        labels = [
            b.text for line in app.transport.messages[-1].reply_markup.inline_keyboard for b in line
        ]
        assert labels[:2] == ["إدارة الخدمات", "أسعار الخدمات"]
        for page in range(3):
            await app.callback(f"admin:readiness:{page}")
            message = app.transport.messages[-1]
            assert tr("catalog_page", page=page + 1, pages=3) in message.text
            async with sessions() as db:
                for line in message.reply_markup.inline_keyboard:
                    for button in line:
                        if button.callback_data.startswith("admin:inspect:"):
                            row = await db.get(Service, button.callback_data.split(":")[-1])
                            assert button.text == row.name_ar
        await app.callback("admin:inspect:text_editing")
        assert "تحرير النصوص" in app.transport.messages[-1].text
        assert tr("catalog_text") in app.transport.messages[-1].text
        assert (await state.get_data())["inputs"] == {"text": "saved"}
        async with sessions() as db:
            assert await db.scalar(select(func.count(Order.id))) == 0
            assert await db.scalar(select(func.count(StarPriceChange.id))) == 0
    finally:
        await app.close()
