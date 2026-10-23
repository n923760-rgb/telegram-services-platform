"""Exercise reordered real intake handlers without Telegram, DB or provider access."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.i18n import tr
from app.services.registry import registry
from tests.test_intake_choice_alias_unit import controls
from tests.test_intake_choice_alias_unit import intake as intake

FILE = "1/" + "a" * 32 + "/source.pdf"


@pytest.fixture(autouse=True)
def database(monkeypatch):
    # These cases exercise saved pre-upgrade PDF choice contracts.
    plugin = registry.types["text_to_pdf"]
    schema = plugin.input_schema.model_copy(deep=True)
    for field in schema.fields:
        field.legacy_only = False
    schema.fields[0].required = True
    monkeypatch.setattr(plugin, "input_schema", schema)
    yield


async def select_service(state, slug):
    plugin = registry.types[slug]
    await state.update_data(
        slug=slug, version=plugin.version, schema=plugin.input_schema.model_dump()
    )


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize(
    "slug,selected",
    [
        ("text_to_pdf", 0),
        ("text_to_pdf", 1),
        ("pdf_tables_excel", 0),
        ("pdf_tables_excel", 1),
        ("pdf_tables_excel", 2),
    ],
)
async def test_mode_precedes_source_and_typed_input_cannot_skip_it(
    intake, monkeypatch, lang, slug, selected
):
    handlers, state, message, callback = intake
    await select_service(state, slug)
    fields = registry.types[slug].input_schema.conversation()
    assert fields[0].name == "mode" and fields[1].name in {"text", "pdf"}
    receive = AsyncMock(return_value=FILE)
    monkeypatch.setattr("app.files.telegram.receive", receive)
    await handlers["resume_callback"](callback, state, lang)
    assert message.answer.call_args.args[0].endswith(tr(fields[0].prompt_key, lang))
    saved = await state.get_data()
    await handlers["collect"](message, state, lang)
    assert message.answer.call_args.args[0] == tr("choose_option", lang)
    assert await state.get_data() == saved
    receive.assert_not_awaited()
    callback.data = f"choice:draft:0:{selected}"
    await handlers["choice"](callback, state, lang)
    assert (await state.get_data())["inputs"] == {"mode": fields[0].choices[selected]}
    assert message.answer.call_args.args[0].endswith(tr(fields[1].prompt_key, lang))
    message.from_user = SimpleNamespace(id=1)
    await handlers["collect"](message, state, lang)
    assert (await state.get_data())["inputs"] == {
        "mode": fields[0].choices[selected],
        fields[1].name: FILE if slug == "pdf_tables_excel" else message.text,
    }
    assert receive.await_count == int(slug == "pdf_tables_excel")


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("slug,selected", [("text_to_pdf", 1), ("pdf_tables_excel", 2)])
async def test_unavailable_mode_blocks_before_source_and_direct_remains_available(
    intake, monkeypatch, lang, slug, selected
):
    handlers, state, message, callback = intake
    await select_service(state, slug)
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=True))
    await handlers["resume_callback"](callback, state, lang)
    saved = await state.get_data()
    assert tr("intake_direct_only", lang) in message.answer.call_args.args[0]
    assert (
        tr(
            "intake_choice_unavailable",
            lang,
            choice=tr(registry.types[slug].input_schema.fields[0].choice_keys[selected], lang),
        )
        == controls(message)[selected].text
    )
    callback.data = f"choice:draft:0:{selected}"
    await handlers["choice"](callback, state, lang)
    assert await state.get_data() == saved
    callback.answer.assert_awaited_with(tr("intake_option_unavailable", lang), show_alert=True)
    callback.data = "choice:draft:0:0"
    await handlers["choice"](callback, state, lang)
    data = await state.get_data()
    assert data["inputs"] == {"mode": "direct"} and data["index"] == 1
    assert data["key"] == saved["key"] and data["price"] == saved["price"]


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("slug", ["text_to_pdf", "pdf_tables_excel"])
async def test_v4_draft_keeps_its_saved_positions_and_source(intake, slug, lang):
    handlers, state, message, callback = intake
    await select_service(state, slug)
    schema = deepcopy((await state.get_data())["schema"])
    schema["fields"][:2] = reversed(schema["fields"][:2])
    source = {"text": "Saved 00123"} if slug == "text_to_pdf" else {"pdf": FILE}
    await state.update_data(schema=schema, version="4", index=1, inputs=source)
    await handlers["resume_callback"](callback, state, lang)
    saved = await state.get_data()
    assert saved["schema"] == schema and saved["version"] == "4"
    assert "choice:draft:1:0" == controls(message)[0].callback_data
    callback.data = "choice:draft:1:0"
    await handlers["choice"](callback, state, lang)
    assert (await state.get_data())["inputs"] == source | {"mode": "direct"}


@pytest.mark.parametrize("slug", ["text_to_pdf", "pdf_tables_excel"])
async def test_failed_mode_prompt_recovers_without_consuming_source(intake, slug):
    handlers, state, message, callback = intake
    await select_service(state, slug)
    message.answer.side_effect = RuntimeError("send failed")
    with pytest.raises(RuntimeError, match="send failed"):
        await handlers["resume_callback"](callback, state)
    assert (await state.get_data())["pending_prompt"]
    message.answer.side_effect = None
    await handlers["collect"](message, state)
    data = await state.get_data()
    assert not data["pending_prompt"] and data["index"] == 0 and data["inputs"] == {}
    assert controls(message)[0].callback_data == "choice:draft:0:0"


@pytest.mark.parametrize("slug", ["text_to_pdf", "pdf_tables_excel"])
async def test_edit_mode_preserves_source_and_abort_restores_review(intake, monkeypatch, slug):
    handlers, state, message, callback = intake
    await select_service(state, slug)
    monkeypatch.setattr("app.bot.handlers.accepted_draft", AsyncMock(return_value=False))
    source = {"text": "Saved 00123"} if slug == "text_to_pdf" else {"pdf": FILE, "language": "ar"}
    original = source | {"mode": "direct"}
    await state.update_data(index=len(registry.types[slug].input_schema.fields), inputs=original)
    await state.set_state("confirm")
    callback.data = "editfield:draft:0"
    await handlers["edit_field"](callback, state)
    saved = await state.get_data()
    assert saved["inputs"] == source
    callback.data = f"editabort:{saved['key']}"
    await handlers["edit_abort"](callback, state)
    assert await state.get_state() == "confirm"
    assert (await state.get_data())["inputs"] == original
