"""Draft review exercises real handlers without accepting a purchase or calling AI."""

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from app.bot.order_review import confirmation_text, input_summary
from app.core.i18n import CATALOGS, tr
from app.services.base import InputField, InputSchema
from app.services.cv_formatting.service import CvFormatting
from app.services.images_to_pdf.service import ImagesToPdf
from app.services.pdf_tools.service import PdfTools
from app.services.registry import registry
from app.services.text_to_word_pdf.service import TextToWordPdf
from tests.test_intake_choice_alias_unit import intake as intake


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("payment", ["test_credit", "stars"])
async def test_real_confirmation_shows_selected_inputs_without_admission(
    intake, lang, payment, monkeypatch
):
    handlers, state, message, callback = intake
    submit = AsyncMock(side_effect=AssertionError("review must not submit"))
    monkeypatch.setattr("app.bot.handlers.submit", submit)
    inputs = {"output_format": "both", "mode": "smart", "text": "PRIVATE body 00123"}
    await state.update_data(
        index=3,
        inputs=inputs,
        payment_mode=payment,
        stars_price=7,
        terms={"ar": "الشروط كاملة", "en": "Complete terms"},
    )
    callback.data = "skip:draft:3"
    await handlers["skip_field"](callback, state, lang)
    text = message.answer.call_args.args[0]
    assert tr("document_output_both", lang) in text
    assert tr("word_pdf_smart", lang) in text
    assert tr("review_text_size", lang, count=len(inputs["text"])) in text
    assert inputs["text"] not in text
    assert (
        tr("stars_confirm", lang, amount=7, terms=(await state.get_data())["terms"][lang]) in text
        if payment == "stars"
        else tr("confirm_price", lang, amount="3.00") in text
    )
    assert message.answer.call_args.kwargs["parse_mode"] is None
    buttons = message.answer.call_args.kwargs["reply_markup"].inline_keyboard
    assert buttons[0][0].callback_data == "confirm:draft"
    assert await state.get_state() == "confirm"
    assert (await state.get_data())["inputs"] == inputs
    submit.assert_not_awaited()


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_conditional_pdf_fields_and_file_order_never_expose_storage_keys(lang):
    inputs = {
        "operation": "merge",
        "files": ["/private/a.pdf", "/private/b.pdf"],
        "file_order": "٢،١",
        "pages": "STALE page",
        "rotation": "90",
    }
    original = deepcopy(inputs)
    result = input_summary(PdfTools.input_schema, inputs, lang)
    assert "«٢،١»" in result and tr("pdf_tools_merge", lang) in result
    assert tr("review_upload_count", lang, count=2) in result
    assert not any(
        value in result
        for value in [
            "/private/",
            "STALE",
            tr("pdf_tools_pages_review", lang),
            tr("pdf_tools_rotation_review", lang),
        ]
    )
    assert inputs == original


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_default_order_and_optional_title_are_explicit(lang):
    result = input_summary(ImagesToPdf.input_schema, {"images": ["secret"]}, lang)
    assert tr("images_pdf_received_order", lang) in result
    result = input_summary(
        TextToWordPdf.input_schema, {"output_format": "word", "text": "body"}, lang
    )
    assert tr("word_pdf_direct", lang) not in result
    assert tr("word_pdf_title_review", lang) in result
    assert tr("review_not_specified", lang) in result


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_titles_are_plain_bounded_inline_and_bulk_cv_data_is_not_repeated(lang):
    inputs = {
        "full_name": "<b>Sam</b>\n\u202ePrice 0\u202c" + "😀" * 200,
        "education": "PRIVATE education",
        "skills": "PRIVATE skills",
        "contact": "PRIVATE phone",
    }
    result = input_summary(CvFormatting.input_schema, inputs, lang)
    assert "\u202e" not in result and "\u202c" not in result
    assert "<b>Sam</b>Price 0" in result and "…»" in result
    assert "PRIVATE" not in result
    assert len(result.encode("utf-16-le")) // 2 <= 1000


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_maximum_stars_terms_remain_exact_and_message_fits_telegram(lang):
    terms = "😀" * 1250  # 2500 UTF-16 units, the configuration maximum.
    inputs = {f"field{i}": "😀" * 120 for i in range(60)}
    schema = InputSchema(
        fields=[
            InputField(name=name, prompt_key="unknown_prompt", single_line=True) for name in inputs
        ]
    )
    data = {
        "slug": "test",
        "schema": schema.model_dump(),
        "inputs": inputs,
        "payment_mode": "stars",
        "stars_price": 99,
        "terms": {lang: terms},
    }
    before = deepcopy(data)
    result = confirmation_text(data, lang)
    assert tr("stars_confirm", lang, amount=99, terms=terms) in result
    assert tr("review_omitted", lang, count=60 - result.count("«")) in result
    assert len(result.encode("utf-16-le")) // 2 < 4096
    assert data == before


def test_nested_conditionals_and_unknown_labels_use_generic_fallback():
    schema = InputSchema(
        fields=[
            InputField(
                name="group",
                kind="form",
                prompt_key="group",
                fields=[InputField(name="text", prompt_key="new_prompt")],
            )
        ]
    )
    result = input_summary(schema, {"group": {"text": "private"}}, "en")
    assert "Input 1: Text received — 7 characters" in result
    assert "new_prompt" not in result
    assert input_summary(schema, {"group": {"text": "private"}}, "en", budget=1) == ""


def test_all_customer_service_review_labels_are_present_in_both_catalogs():
    for service in registry.types.values():
        if service.admin_only:
            continue
        for field in service.input_schema.conversation():
            for lang in ("ar", "en"):
                assert field.prompt_key + "_review" in CATALOGS[lang]


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_failed_confirmation_send_recovers_same_summary_and_purchase_key(intake, lang):
    handlers, state, message, callback = intake
    inputs = {"output_format": "pdf", "mode": "direct", "text": "Original 00123"}
    await state.update_data(index=3, inputs=inputs)
    callback.data = "skip:draft:3"
    message.answer.side_effect = RuntimeError("temporary delivery failure")
    with pytest.raises(RuntimeError, match="temporary delivery failure"):
        await handlers["skip_field"](callback, state, lang)
    original_text = message.answer.call_args.args[0]
    assert (await state.get_data())["pending_prompt"]
    message.answer.side_effect = None
    await handlers["confirm_prompt"](message, state, lang)
    assert message.answer.call_args.args[0] == original_text
    data = await state.get_data()
    assert not data["pending_prompt"] and data["key"] == "draft"
    assert data["inputs"] == inputs and await state.get_state() == "confirm"


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_requested_slide_count_and_title_are_visible_without_echoing_body(lang):
    from app.services.text_to_pptx.service import TextToPptx

    result = input_summary(TextToPptx.input_schema, {"slide_count": "١٢", "text": "PRIVATE"}, lang)
    assert tr("pptx_slide_count_review", lang) + ": «١٢»" in result
    result = input_summary(
        TextToWordPdf.input_schema,
        {"output_format": "pdf", "text": "PRIVATE", "title": "تقرير 00123"},
        lang,
    )
    assert "«تقرير 00123»" in result and "PRIVATE" not in result
