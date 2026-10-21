"""Early hints use declarations; complete validated input still owns admission."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from app.bot import availability
from app.core.i18n import tr
from app.core.settings import config
from app.services.base import validate_ai_intake_choices
from app.services.registry import Registry, registry
from tests.test_intake_choice_alias_unit import controls
from tests.test_intake_choice_alias_unit import intake as intake
from tests.test_service_ai_policy_unit import CASES


@pytest.fixture(autouse=True)
def database():
    yield


def draft(slug, **changes):
    plugin = registry.types[slug]
    return dict(
        slug=slug, version=plugin.version, schema=plugin.input_schema.model_dump(), **changes
    )


@pytest.mark.parametrize(
    "slug,inputs,expected", [c for c in CASES if registry.types[c[0]].optional_ai]
)
def test_current_hints_cover_validated_mixed_service_decisions(slug, inputs, expected):
    plugin = registry.types[slug]
    plugin.input_schema.validate_inputs(inputs)
    validate_ai_intake_choices(plugin)
    hints = availability.declared_ai_choices(draft(slug))
    assert any(inputs.get(name) in values for name, values in hints.items()) is expected
    assert plugin.needs_ai(inputs) is expected


@pytest.mark.parametrize(
    "mapping",
    [
        None,
        [],
        {"missing": ("smart",)},
        {"mode": []},
        {"mode": ()},
        {"mode": ("unknown",)},
        {"mode": ("smart", "smart")},
        {"mode": (1,)},
    ],
)
def test_invalid_choice_declaration_is_rejected_at_discovery(monkeypatch, mapping):
    monkeypatch.setattr(registry.types["text_to_word_pdf"], "ai_intake_choices", mapping)
    with pytest.raises(ValueError, match="invalid AI intake choices"):
        Registry().discover()


def test_declarations_require_conditional_ai_policy(monkeypatch):
    monkeypatch.setattr(registry.types["echo"], "ai_intake_choices", {"text": ("smart",)})
    with pytest.raises(ValueError, match="invalid AI intake choices"):
        Registry().discover()


@pytest.mark.parametrize("change", ["version", "schema", "unknown", "direct"])
async def test_unrelated_or_stale_draft_does_not_read_pause_state(monkeypatch, change):
    data = draft("text_to_word_pdf")
    if change == "schema":
        data["schema"]["fields"][0]["prompt_key"] = "different_prompt"
    elif change == "version":
        data["version"] = "old"
    else:
        data = draft("csv_review") if change == "direct" else {"slug": "unknown"}
    monkeypatch.setattr(availability, "sessions", lambda: pytest.fail("unexpected DB query"))
    assert availability.declared_ai_choices(data) == {}
    assert not await availability.mixed_ai_unavailable(data)


async def test_disabled_ai_warns_without_database(monkeypatch):
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(availability, "sessions", lambda: pytest.fail("unexpected DB query"))
    assert await availability.mixed_ai_unavailable(draft("text_to_word_pdf"))


async def test_pause_and_resume_are_read_afresh_without_draft_mutation(monkeypatch):
    monkeypatch.setattr(config(), "ai_enabled", True)
    check = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr(availability, "ai_admission_available", check)
    db = object()

    @asynccontextmanager
    async def session():
        yield db

    monkeypatch.setattr(availability, "sessions", session)
    data = draft("text_to_word_pdf", inputs={"text": "Source"})
    assert await availability.mixed_ai_unavailable(data)
    assert not await availability.mixed_ai_unavailable(data)
    assert data == draft("text_to_word_pdf", inputs={"text": "Source"})
    assert check.await_args_list[0].args == (db,)


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_blocked_choice_preserves_draft_then_same_button_works_after_resume(
    intake, monkeypatch, lang
):
    handlers, state, message, callback = intake
    check = AsyncMock(return_value=True)
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", check)
    await handlers["choice"](callback, state, lang)  # output format remains available
    assert tr("intake_direct_only", lang) in message.answer.call_args.args[0]
    buttons = controls(message)
    assert buttons[0].text == tr("word_pdf_direct", lang)
    assert buttons[1].text == tr(
        "intake_choice_unavailable", lang, choice=tr("word_pdf_smart", lang)
    )
    saved = await state.get_data()
    count = message.answer.await_count
    callback.data = "choice:draft:1:1"
    await handlers["choice"](callback, state, lang)
    callback.answer.assert_awaited_with(tr("intake_option_unavailable", lang), show_alert=True)
    assert await state.get_data() == saved
    assert await state.get_state() == "collect"
    assert message.answer.await_count == count
    check.return_value = False
    await handlers["choice"](callback, state, lang)
    assert (await state.get_data())["inputs"] == {"output_format": "word", "mode": "smart"}
    assert tr("intake_direct_only", lang) not in message.answer.call_args.args[0]


@pytest.mark.parametrize("slug", ["text_to_pdf", "pdf_tables_excel"])
@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_first_mode_prompt_warns_before_text_or_upload(intake, monkeypatch, slug, lang):
    handlers, state, message, callback = intake
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=True))
    data = await state.get_data()
    data.update(draft(slug))
    await state.set_data(data)
    await handlers["resume_callback"](callback, state, lang)
    text = message.answer.call_args.args[0]
    assert tr("intake_direct_only", lang) in text
    assert text.endswith(tr(registry.types[slug].input_schema.conversation()[0].prompt_key, lang))
    assert (await state.get_data())["inputs"] == {}


@pytest.mark.parametrize("legacy_skip", [False, True])
async def test_direct_choice_and_legacy_skip_continue_during_pause(
    intake, monkeypatch, legacy_skip
):
    handlers, state, message, callback = intake
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=True))
    await handlers["choice"](callback, state)
    callback.data = "skip:draft:1" if legacy_skip else "choice:draft:1:0"
    await handlers["skip_field" if legacy_skip else "choice"](callback, state)
    assert (await state.get_data())["index"] == 2
    assert (await state.get_data())["inputs"] == {"output_format": "word"} | (
        {} if legacy_skip else {"mode": "direct"}
    )


async def test_marked_optional_skip_alias_cannot_bypass_warning(intake, monkeypatch):
    handlers, state, message, callback = intake
    plugin = registry.types["text_to_word_pdf"]
    monkeypatch.setattr(plugin, "ai_intake_choices", {"mode": ("direct",)})
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=True))
    await handlers["choice"](callback, state)
    saved = await state.get_data()
    callback.data = "skip:draft:1"
    await handlers["skip_field"](callback, state)
    assert await state.get_data() == saved
    assert message.answer.call_args.args[0] == tr("intake_option_unavailable")


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_edit_block_preserves_source_and_allows_return_without_changes(
    intake, monkeypatch, lang
):
    handlers, state, message, callback = intake
    monkeypatch.setattr("app.bot.handlers.accepted_draft", AsyncMock(return_value=False))
    monkeypatch.setattr("app.bot.handlers.mixed_ai_unavailable", AsyncMock(return_value=True))
    original = {"output_format": "both", "mode": "direct", "text": "Saved 00123"}
    await state.update_data(index=4, inputs=original)
    await state.set_state("confirm")
    callback.data = "editfield:draft:1"
    await handlers["edit_field"](callback, state, lang)
    saved = await state.get_data()
    key = saved["key"]
    callback.data = f"choice:{key}:1:1"
    await handlers["choice"](callback, state, lang)
    assert await state.get_data() == saved
    assert saved["inputs"]["text"] == original["text"]
    callback.data = f"editabort:{key}"
    await handlers["edit_abort"](callback, state, lang)
    assert await state.get_state() == "confirm"
    assert (await state.get_data())["inputs"] == original
