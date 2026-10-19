from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.pdf_to_word.test_service import SOURCE, configured_service, pdf_bytes
from tests.pdf_form_fixtures import form_pdf


@pytest.fixture(autouse=True)
def database():
    yield


def test_real_field_value_is_not_part_of_extracted_page_text():
    reader = PdfReader(BytesIO(form_pdf()))
    assert reader.get_fields()["account"]["/V"] == "Account 00999"
    assert SOURCE in reader.pages[0].extract_text()
    assert "00999" not in reader.pages[0].extract_text()


@pytest.mark.parametrize("kind", ["acroform", "widget", "permissions", "empty_form"])
@pytest.mark.parametrize("later", [False, True])
async def test_forms_are_rejected_before_ai_or_output(tmp_path, kind, later):
    service, source, store, ai = configured_service(tmp_path, form_pdf(kind, later=later))
    with pytest.raises(ServiceError, match="pdf_word_form"):
        await service.run({"pdf": source.key})
    ai.extract.assert_not_awaited()
    assert store.storage.usage(1)[1] == 1


@pytest.mark.parametrize("malformed", [True, False])
async def test_annotation_parsing_is_fail_closed_but_ordinary_links_remain_supported(
    tmp_path, malformed
):
    writer = PdfWriter(clone_from=PdfReader(BytesIO(pdf_bytes())))
    link = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([NumberObject(n) for n in (30, 740, 200, 760)]),
            NameObject("/A"): DictionaryObject(
                {
                    NameObject("/S"): NameObject("/URI"),
                    NameObject("/URI"): TextStringObject("https://example.invalid"),
                }
            ),
        }
    )
    annotations = ArrayObject([TextStringObject("broken") if malformed else link])
    # An indirect annotation array is legal and must also be inspected.
    writer.pages[0][NameObject("/Annots")] = writer._add_object(annotations)
    output = BytesIO()
    writer.write(output)
    service, source, store, ai = configured_service(tmp_path, output.getvalue())
    if malformed:
        with pytest.raises(ServiceError, match="file_invalid"):
            await service.run({"pdf": source.key})
        ai.extract.assert_not_awaited()
        assert store.storage.usage(1)[1] == 1
    else:
        result = await service.run({"pdf": source.key})
        assert store.read(result.artifacts[0].key)
        ai.extract.assert_awaited_once()


@pytest.mark.parametrize("language", ["ar", "en"])
def test_intake_and_error_disclose_form_and_signature_limits(language):
    assert tr("pdf_word_form", language) != "pdf_word_form"
    assert ("توقيع" if language == "ar" else "signature") in tr("pdf_word_form", language)
    assert ("النماذج" if language == "ar" else "forms") in tr("pdf_to_word_file", language)
