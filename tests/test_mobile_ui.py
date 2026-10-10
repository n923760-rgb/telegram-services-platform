from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.bot.ui import buttons
from app.core.display import message_parts, order_reference, result_preview
from app.core.i18n import tr
from app.providers.delivery import TelegramDelivery
from app.services.base import Result

REFERENCE = UUID("6c7382cc-ee7f-4206-b528-cdc51a150506")


@pytest.mark.parametrize("text", ["hello", "مرحبا" * 1800, "🙂" * 3000, "a🙂ب" * 2000])
def test_utf16_message_parts_preserve_all_content(text):
    parts = list(message_parts(text))
    assert "".join(parts) == text
    assert all(0 < len(part.encode("utf-16-le")) // 2 <= 3500 for part in parts)


@pytest.mark.parametrize("value", [REFERENCE, str(REFERENCE)])
def test_short_display_reference_does_not_change_identifier(value):
    assert order_reference(value) == "6C7382CC"
    assert str(REFERENCE) == "6c7382cc-ee7f-4206-b528-cdc51a150506"


def test_legacy_arbitrary_display_reference():
    assert order_reference("order") == "order"


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_choice_labels_fit_and_cancel_is_separate(lang):
    items = [
        (tr(key, lang), f"choice:{i}")
        for i, key in enumerate(["pdf_tables_lattice", "pdf_tables_stream", "pdf_tables_labels"])
    ] + [(tr("cancel", lang), "cancel:full-draft-id")]
    markup = buttons(items, columns=2, separate_last=True)
    assert markup.inline_keyboard[-1][0].callback_data == "cancel:full-draft-id"
    assert len(markup.inline_keyboard[-1]) == 1
    assert [b.callback_data for row in markup.inline_keyboard for b in row] == [
        item[1] for item in items
    ]
    for row in markup.inline_keyboard:
        assert len(row) == 1 or all(len(b.text) <= 18 for b in row)


def test_long_choices_get_full_width_without_truncation():
    text = "A descriptive choice that cannot fit in half a row"
    markup = buttons([("Short", "a"), (text, "b"), ("Small", "c")], columns=2)
    assert [len(row) for row in markup.inline_keyboard] == [1, 1, 1]
    assert markup.inline_keyboard[1][0].text == text


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_confirmation_splits_all_preview_text_and_preserves_full_callbacks(lang):
    bot = AsyncMock()
    delivery = TelegramDelivery(bot)
    delivery._lang = AsyncMock(return_value=lang)
    preview = "🙂" * 2900 + "LAST COLUMN"
    await delivery.confirmation(1, REFERENCE, preview)
    calls = bot.send_message.await_args_list
    assert len(calls) >= 2
    combined = "".join(call.args[1] for call in calls)
    assert preview in combined and "6C7382CC" in combined and str(REFERENCE) not in combined
    assert all(len(call.args[1].encode("utf-16-le")) // 2 <= 3500 for call in calls)
    assert all(call.kwargs["reply_markup"] is None for call in calls[:-1])
    rows = calls[-1].kwargs["reply_markup"].inline_keyboard
    assert [len(row) for row in rows] == [1, 1]
    assert rows[0][0].callback_data == f"approve:{REFERENCE}"
    assert rows[1][0].callback_data == f"reject:{REFERENCE}"


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_delivery_uses_ui_language_for_preview_without_translating_customer_text(lang):
    bot = AsyncMock()
    delivery = TelegramDelivery(bot)
    delivery._lang = AsyncMock(return_value=lang)
    result = Result(
        text="Original customer text",
        preview="legacy",
        preview_localizations={"ar": "ملخص عربي", "en": "English preview"},
    )
    await delivery.send(1, REFERENCE, result)
    texts = [call.args[1] for call in bot.send_message.await_args_list]
    assert result.preview_localizations[lang] in texts[1]
    assert texts[-1] == result.text and "6C7382CC" in texts[0]


@pytest.mark.parametrize("localizations", [{"ar": "x" * 3001}, {"en": "x" * 3001}, {"fr": "text"}])
def test_localized_preview_contract_is_bounded(localizations):
    with pytest.raises(ValidationError):
        Result(text="content", preview_localizations=localizations)


def test_prepared_legacy_results_keep_their_preview():
    assert result_preview({"preview": "Legacy"}, "ar") == "Legacy"
    assert (
        result_preview({"preview": "Legacy", "preview_localizations": {"en": "New"}}, "ar")
        == "Legacy"
    )
