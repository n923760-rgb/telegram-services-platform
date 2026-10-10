from decimal import Decimal

from app.builders.word_schema import WordDocument
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema
from app.services.document_results import word_pdf_result
from app.services.text_to_word_pdf.schema import Inputs


class TextToWordPdf(BaseService):
    slug = "text_to_word_pdf"
    name_ar = tr("word_pdf_name")
    name_en = tr("word_pdf_name", "en")
    description_ar = tr("word_pdf_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="word_pdf_text"),
            InputField(
                name="title",
                prompt_key="word_pdf_title",
                required=False,
                max_length=200,
                single_line=True,
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        return await word_pdf_result(
            self.runtime,
            WordDocument.model_validate(values.document().model_dump()),
            include_title=values.title is not None,
            preview=tr("word_pdf_preview"),
            preview_localizations=translations("word_pdf_preview"),
        )


SERVICE = TextToWordPdf
