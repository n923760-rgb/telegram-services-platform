"""Exercise real intake handlers without a DB, provider or Telegram connection."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import create_router
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.text_to_word_pdf.service import TextToWordPdf


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.fixture
async def intake(monkeypatch):
    # A saved pre-upgrade draft retains its original prompts and choice guards.
    schema = TextToWordPdf.input_schema.model_copy(deep=True)
    for field in schema.fields:
        field.legacy_only = False
    monkeypatch.setattr(TextToWordPdf, "input_schema", schema)
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=False))
    router = create_router()
    storage = MemoryStorage()
    state = FSMContext(storage, StorageKey(bot_id=42, chat_id=1, user_id=1))
    await state.set_state("collect")
    await state.set_data(
        {
            "schema": TextToWordPdf.input_schema.model_dump(),
            "index": 0,
            "inputs": {},
            "key": "draft",
            "slug": TextToWordPdf.slug,
            "price": 300,
            "version": TextToWordPdf.version,
        }
    )
    handlers = {
        item.callback.__name__: item.callback
        for observer in (router.callback_query, router.message)
        for item in observer.handlers
    }
    message = SimpleNamespace(answer=AsyncMock(), text="Source 00123")
    callback = SimpleNamespace(
        data="choice:draft:0:1",
        message=message,
        answer=AsyncMock(),
        from_user=SimpleNamespace(id=1),
    )
    yield handlers, state, message, callback
    await storage.close()


def controls(message):
    return [
        button
        for row in message.answer.call_args.kwargs["reply_markup"].inline_keyboard
        for button in row
    ]


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("mode", ["direct", "smart", "legacy_skip"])
async def test_mode_has_one_preserve_button_and_both_choices_advance(intake, lang, mode):
    handlers, state, message, callback = intake
    await handlers["choice"](callback, state, lang)
    buttons = controls(message)
    assert [b.text for b in buttons] == [
        tr("word_pdf_direct", lang),
        tr("word_pdf_smart", lang),
        tr("cancel", lang),
    ]
    assert [b.callback_data for b in buttons] == [
        "choice:draft:1:0",
        "choice:draft:1:1",
        "cancel:draft",
    ]
    assert message.answer.call_args.args[0].endswith(tr("word_pdf_mode", lang))
    if mode == "legacy_skip":
        callback.data = "skip:draft:1"
        await handlers["skip_field"](callback, state, lang)
    else:
        callback.data = "choice:draft:1:" + str(int(mode == "smart"))
        await handlers["choice"](callback, state, lang)
    data = await state.get_data()
    assert data["inputs"] == {"output_format": "word"} | (
        {} if mode == "legacy_skip" else {"mode": mode}
    )
    assert data["index"] == 2 and not data["pending_prompt"]
    assert message.answer.call_args.args[0].endswith(tr("word_pdf_text", lang))
    await handlers["collect"](message, state, lang)
    assert (await state.get_data())["inputs"]["text"] == message.text
    assert any(b.callback_data == "skip:draft:3" for b in controls(message))
    callback.data = "skip:draft:3"
    await handlers["skip_field"](callback, state, lang)
    assert await state.get_state() == "confirm"
    assert "title" not in (await state.get_data())["inputs"]


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_distinct_optional_skip_is_still_visible_and_usable(intake, lang):
    handlers, state, message, callback = intake
    data = await state.get_data()
    data["schema"]["fields"][1]["skip_key"] = "skip_field"
    await state.set_data(data)
    await handlers["choice"](callback, state, lang)
    buttons = controls(message)
    assert [b.text for b in buttons] == [
        tr("word_pdf_direct", lang),
        tr("word_pdf_smart", lang),
        tr("skip_field", lang),
        tr("cancel", lang),
    ]
    callback.data = "skip:draft:1"
    await handlers["skip_field"](callback, state, lang)
    assert (await state.get_data())["inputs"] == {"output_format": "word"}
    assert message.answer.call_args.args[0].endswith(tr("word_pdf_text", lang))


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_unavailable_submission_keeps_draft_and_does_not_show_queued(
    intake, lang, monkeypatch
):
    handlers, state, message, callback = intake
    submit = AsyncMock(side_effect=ServiceError("provider_config"))
    monkeypatch.setattr("app.bot.handlers.submit", submit)
    data = await state.get_data()
    data.update(index=4, inputs={"output_format": "word", "mode": "smart", "text": "Source"})
    await state.set_data(data)
    await state.set_state("confirm")
    callback.data = "confirm:draft"
    await handlers["confirm"](callback, state, lang)
    submit.assert_awaited_once()
    assert message.answer.call_args.args[0] == tr("provider_config", lang)
    assert message.answer.await_count == 1
    assert await state.get_state() == "confirm"
    assert await state.get_data() == data
