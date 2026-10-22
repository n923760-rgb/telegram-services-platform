"""Edit real draft handlers without database, Telegram or provider calls."""

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from app.bot.draft_edit import abort_edit, advance, begin_edit, next_index
from app.core.i18n import tr
from app.services.base import InputField, InputSchema
from app.services.text_to_office.service import TextToOffice
from tests.test_intake_choice_alias_unit import controls
from tests.test_intake_choice_alias_unit import intake as intake


@pytest.fixture(autouse=True)
def database(monkeypatch):
    monkeypatch.setattr("app.bot.handlers.accepted_draft", AsyncMock(return_value=False))
    yield


async def confirmed(state, inputs=None):
    data = await state.get_data()
    data.update(
        index=4,
        inputs=inputs
        or {"output_format": "both", "mode": "smart", "text": "PRIVATE 00123", "title": "Title"},
    )
    await state.set_data(data)
    await state.set_state("confirm")
    return deepcopy(data)


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("payment", ["test_credit", "stars"])
async def test_edit_format_preserves_text_and_title_and_invalidates_old_confirm(
    intake, lang, payment, monkeypatch
):
    handlers, state, message, callback = intake
    submit = AsyncMock(side_effect=AssertionError("editing must not purchase"))
    monkeypatch.setattr("app.bot.handlers.submit", submit)
    original = await confirmed(state)
    await state.update_data(
        payment_mode=payment, stars_price=9, terms={"ar": "شروط", "en": "Terms"}
    )
    callback.data = "edit:draft"
    await handlers["edit_menu"](callback, state, lang)
    assert [b.callback_data for b in controls(message)][0] == "editfield:draft:0"
    assert "PRIVATE" not in message.answer.call_args.args[0]
    callback.data = "editfield:draft:0"
    await handlers["edit_field"](callback, state, lang)
    data = await state.get_data()
    key = data["key"]
    assert key != "draft" and await state.get_state() == "collect"
    assert data["inputs"] == {k: v for k, v in original["inputs"].items() if k != "output_format"}
    callback.data = f"choice:{key}:0:1"
    await handlers["choice"](callback, state, lang)
    data = await state.get_data()
    assert await state.get_state() == "confirm"
    assert data["inputs"] == original["inputs"] | {"output_format": "word"}
    assert "_edit_queue" not in data and "_edit_original" not in data
    assert data["payment_mode"] == payment and data["stars_price"] == 9
    callback.data = "confirm:draft"
    await handlers["confirm"](callback, state, lang)
    assert message.answer.call_args.args[0] == tr("stale_button", lang)
    submit.assert_not_awaited()


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_text_edit_returns_directly_to_review_and_abort_restores_original(intake, lang):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    callback.data = "editfield:draft:2"
    await handlers["edit_field"](callback, state, lang)
    first_key = (await state.get_data())["key"]
    callback.data = f"editabort:{first_key}"
    await handlers["edit_abort"](callback, state, lang)
    restored = await state.get_data()
    assert restored["inputs"] == original["inputs"]
    assert restored["key"] not in {first_key, "draft"}
    callback.data = f"editfield:{restored['key']}:2"
    await handlers["edit_field"](callback, state, lang)
    message.text = "Replacement 00123"
    await handlers["collect"](message, state, lang)
    assert await state.get_state() == "confirm"
    assert (await state.get_data())["inputs"] == original["inputs"] | {"text": message.text}


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("selected", ["word", "excel"])
async def test_conditional_mode_is_recollected_or_removed_but_source_is_retained(
    intake, lang, selected
):
    handlers, state, message, callback = intake
    data = await confirmed(state, {"target": "word", "mode": "smart", "text": "Preserved source"})
    data["schema"] = TextToOffice.input_schema.model_dump()
    await state.set_data(data)
    callback.data = "editfield:draft:0"
    await handlers["edit_field"](callback, state, lang)
    key = (await state.get_data())["key"]
    callback.data = f"choice:{key}:0:{int(selected == 'excel')}"
    await handlers["choice"](callback, state, lang)
    if selected == "word":
        assert await state.get_state() == "collect"
        assert (await state.get_data())["index"] == 1
        callback.data = f"choice:{key}:1:0"
        await handlers["choice"](callback, state, lang)
    assert await state.get_state() == "confirm"
    inputs = (await state.get_data())["inputs"]
    assert inputs["target"] == selected and inputs["text"] == "Preserved source"
    assert ("mode" in inputs) == (selected == "word")


@pytest.mark.parametrize("suffix", ["-1", "99", "01", "١", "x", "0:extra"])
async def test_malformed_or_out_of_range_edit_is_rejected_without_mutation(intake, suffix):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    callback.data = f"editfield:draft:{suffix}"
    await handlers["edit_field"](callback, state, "en")
    assert await state.get_data() == original
    assert callback.answer.call_args.args[0] == tr("invalid_request", "en")


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("stage", ["start", "finish", "abort"])
async def test_failed_send_recovers_edit_or_review_without_reapplying_input(intake, lang, stage):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    callback.data = "editfield:draft:2"
    if stage == "start":
        message.answer.side_effect = RuntimeError("transport")
        with pytest.raises(RuntimeError):
            await handlers["edit_field"](callback, state, lang)
    else:
        await handlers["edit_field"](callback, state, lang)
        message.answer.side_effect = RuntimeError("transport")
        with pytest.raises(RuntimeError):
            if stage == "finish":
                message.text = "Replacement"
                await handlers["collect"](message, state, lang)
            else:
                callback.data = f"editabort:{(await state.get_data())['key']}"
                await handlers["edit_abort"](callback, state, lang)
    failed = await state.get_data()
    assert failed["pending_prompt"]
    message.answer.side_effect = None
    handler = handlers["collect"] if stage == "start" else handlers["confirm_prompt"]
    await handler(message, state, lang)
    data = await state.get_data()
    assert data["inputs"] == failed["inputs"] and data["key"] == failed["key"]
    assert not data["pending_prompt"]
    assert (
        data["inputs"].get("text")
        == ({"start": None, "finish": "Replacement", "abort": original["inputs"]["text"]}[stage])
    )


def test_nested_transitive_conditions_remain_queued_until_parent_is_answered():
    schema = InputSchema(
        fields=[
            InputField(name="kind", prompt_key="kind", choices=["a", "b"], choice_keys=["a", "b"]),
            InputField(
                name="group",
                kind="form",
                prompt_key="group",
                when={"kind": ["a"]},
                fields=[InputField(name="value", prompt_key="value")],
            ),
            InputField(name="last", prompt_key="last", when={"group.value": ["yes"]}),
            InputField(name="unrelated", prompt_key="unrelated"),
        ]
    )
    original = {
        "schema": schema.model_dump(),
        "inputs": {"kind": "a", "group": {"value": "yes"}, "last": "old", "unrelated": "keep"},
        "index": 4,
    }
    data = begin_edit(original, 0)
    assert next_index(data, schema.conversation()) == 0
    assert data["_edit_queue"] == [0, 1, 2]
    data["inputs"]["kind"] = "a"
    advance(data)
    assert next_index(data, schema.conversation()) == 1
    data["inputs"]["group"]["value"] = "yes"
    advance(data)
    assert next_index(data, schema.conversation()) == 2
    assert abort_edit(data) == original
    assert original["inputs"]["last"] == "old" and data["inputs"]["unrelated"] == "keep"


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_optional_title_can_be_cleared_without_recollecting_other_fields(intake, lang):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    callback.data = "editfield:draft:3"
    await handlers["edit_field"](callback, state, lang)
    callback.data = f"skip:{(await state.get_data())['key']}:3"
    await handlers["skip_field"](callback, state, lang)
    assert await state.get_state() == "confirm"
    assert (await state.get_data())["inputs"] == {
        k: v for k, v in original["inputs"].items() if k != "title"
    }


@pytest.mark.parametrize("abort", [False, True])
async def test_upload_edit_uses_existing_receive_done_and_abort_paths(intake, abort, monkeypatch):
    from app.services.images_to_pdf.service import ImagesToPdf

    handlers, state, message, callback = intake
    original_inputs = {"images": ["old-a", "old-b"], "page_order": "2,1", "orientation": "portrait"}
    data = await confirmed(state, original_inputs)
    data["schema"] = ImagesToPdf.input_schema.model_dump()
    await state.set_data(data)
    message.from_user = callback.from_user
    receive = AsyncMock(side_effect=["new-a", "new-b"])
    monkeypatch.setattr("app.files.telegram.receive", receive)
    callback.data = "editfield:draft:0"
    await handlers["edit_field"](callback, state, "en")
    key = (await state.get_data())["key"]
    await handlers["collect"](message, state, "en")
    assert (await state.get_data())["inputs"]["images"] == ["new-a"]
    assert any(b.callback_data == f"done:{key}:0" for b in controls(message))
    if abort:
        callback.data = f"editabort:{key}"
        await handlers["edit_abort"](callback, state, "en")
        assert (await state.get_data())["inputs"] == original_inputs
    else:
        await handlers["collect"](message, state, "en")
        callback.data = f"done:{key}:0"
        await handlers["done_files"](callback, state, "en")
        assert (await state.get_data())["inputs"] == original_inputs | {
            "images": ["new-a", "new-b"]
        }
    assert await state.get_state() == "confirm"
    assert original_inputs["images"] == ["old-a", "old-b"]


@pytest.mark.parametrize("action", ["edit_menu", "edit_field", "edit_abort"])
async def test_stale_edit_controls_do_not_modify_current_draft(intake, action):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    callback.data = {
        "edit_menu": "edit:old",
        "edit_field": "editfield:old:0",
        "edit_abort": "editabort:old",
    }[action]
    await handlers[action](callback, state, "en")
    assert await state.get_data() == original
    assert callback.answer.call_args.args[0] == tr("stale_button", "en")


def test_inactive_field_cannot_be_selected_for_editing():
    data = {
        "schema": TextToOffice.input_schema.model_dump(),
        "inputs": {"target": "excel", "text": "Source"},
        "index": 3,
    }
    with pytest.raises(ValueError):
        begin_edit(data, 1)


@pytest.mark.parametrize("action", ["edit_menu", "edit_field"])
async def test_accepted_request_cannot_rotate_key_or_change_inputs(intake, monkeypatch, action):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    accepted = AsyncMock(return_value=True)
    monkeypatch.setattr("app.bot.handlers.accepted_draft", accepted)
    callback.data = "edit:draft" if action == "edit_menu" else "editfield:draft:2"
    await handlers[action](callback, state, "en")
    accepted.assert_awaited_once_with(callback.from_user.id, "draft")
    assert await state.get_data() == original
    assert callback.answer.call_args.args[0] == tr("review_edit_submitted", "en")


async def test_unavailable_acceptance_read_fails_closed_without_rotating_key(intake, monkeypatch):
    handlers, state, message, callback = intake
    original = await confirmed(state)
    monkeypatch.setattr(
        "app.bot.handlers.accepted_draft", AsyncMock(side_effect=RuntimeError("db unavailable"))
    )
    callback.data = "editfield:draft:2"
    with pytest.raises(RuntimeError, match="db unavailable"):
        await handlers["edit_field"](callback, state, "en")
    assert await state.get_data() == original
