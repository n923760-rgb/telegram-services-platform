"""Explicit Word choices and legacy internal parsing, without a provider or DB."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from docx import Document

from app.core.i18n import tr
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError, active_field
from app.services.text_to_office.schema import Inputs
from app.services.text_to_office.service import TextToOffice


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("mode", ["direct", "smart"])
def test_word_requires_a_visible_mode_and_routes_it_without_changing_source(mode):
    inputs = {"target": "word", "mode": mode, "text": "بدون تعديل النص\nSource 00123"}
    TextToOffice.input_schema.validate_inputs(inputs)
    parsed = Inputs.parse(inputs)
    assert parsed.mode == mode and parsed.text == inputs["text"]
    assert TextToOffice.needs_ai(inputs) is (mode == "smart")


@pytest.mark.parametrize("mode", [None, "", "automatic", "DIRECT"])
def test_new_word_orders_cannot_skip_or_forge_mode(mode):
    inputs = {"target": "word", "text": "Source"}
    if mode is not None:
        inputs["mode"] = mode
    with pytest.raises(ServiceError, match="input_invalid"):
        TextToOffice.input_schema.validate_inputs(inputs)


def test_excel_skips_word_choices_but_still_needs_ai():
    inputs = {"target": "excel", "text": "00123 | 125.50"}
    fields = TextToOffice.input_schema.conversation()
    assert [field.name for field in fields if active_field(field, inputs)] == ["target", "text"]
    TextToOffice.input_schema.validate_inputs(inputs)
    assert TextToOffice.needs_ai(inputs)
    for mode in ("direct", "smart"):
        with pytest.raises(ServiceError, match="invalid_request"):
            TextToOffice.input_schema.validate_inputs(inputs | {"mode": mode})


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_word_mode_is_required_localized_and_precedes_content(lang):
    fields = TextToOffice.input_schema.conversation()
    assert [field.name for field in fields] == ["target", "mode", "text"]
    assert fields[1].required and fields[1].when == {"target": ["word"]}
    for key in (fields[1].prompt_key, *fields[1].choice_keys):
        assert tr(key, lang) != key
    assert "Keep text unchanged" not in tr("office_text", lang)
    assert "بدون تعديل النص»" not in tr("office_text", lang)


@pytest.mark.parametrize("phrase", ["بدون تعديل النص", "Keep text unchanged:"])
def test_legacy_internal_requests_retain_their_parser(phrase):
    inputs = {"target": "word", "text": phrase + "\n  Source 00123  "}
    assert Inputs.parse(inputs).text == "  Source 00123  "
    assert not TextToOffice.needs_ai(inputs)
    assert TextToOffice.needs_ai({"target": "word", "text": "Source"})


@pytest.mark.parametrize("phrase", ["بدون تعديل النص", "Keep text unchanged"])
async def test_explicit_direct_output_keeps_even_legacy_instruction_lines_as_content(
    tmp_path, phrase
):
    text = phrase + "\n  نص 00123\n\nEnglish <tag> & 125.50  "
    inputs = {"target": "word", "mode": "direct", "text": text}
    TextToOffice.input_schema.validate_inputs(inputs)
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    ai = SimpleNamespace(extract=AsyncMock(side_effect=AssertionError("unexpected AI")))
    service = TextToOffice()
    service.runtime = SimpleNamespace(storage=store, ai=ai)
    result = await service.run(inputs)
    ai.extract.assert_not_awaited()
    document = Document(BytesIO(store.read(result.artifacts[0].key)))
    assert "\n".join(p.text for p in document.paragraphs) == text
    assert not result.needs_confirmation
