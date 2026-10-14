from decimal import Decimal

from pydantic import ValidationError

from app.builders.word_schema import WordDocument
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, ServiceError
from app.services.document_results import word_pdf_result
from app.services.text_to_word_pdf.prompt import REFINE
from app.services.text_to_word_pdf.schema import Inputs, refined_document, revision_schema


class TextToWordPdf(BaseService):
    version = "2"
    slug = "text_to_word_pdf"
    worker_requirements = ("office_export",)
    menu_order = 30
    category = "documents"
    name_ar = tr("word_pdf_name")
    name_en = tr("word_pdf_name", "en")
    description_ar = tr("word_pdf_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="mode",
                prompt_key="word_pdf_mode",
                required=False,
                skip_key="word_pdf_direct",
                choices=["direct", "smart"],
                choice_keys=["word_pdf_direct", "word_pdf_smart"],
            ),
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
        return Inputs.parse(inputs).mode == "smart"

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        if values.mode == "smart":
            if self.runtime.ai is None:
                raise ServiceError("provider_config")
            schema = revision_schema(values)
            revision = await self.runtime.ai.extract(schema, values.source(), REFINE)
            try:
                revision = schema.model_validate(revision.model_dump(mode="json"))
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
            return await word_pdf_result(
                self.runtime,
                refined_document(revision),
                preview=tr("word_pdf_smart_preview"),
                preview_localizations=translations("word_pdf_smart_preview"),
            )
        return await word_pdf_result(
            self.runtime,
            WordDocument.model_validate(values.document().model_dump()),
            include_title=values.title is not None,
            preview=tr("word_pdf_preview"),
            preview_localizations=translations("word_pdf_preview"),
        )


SERVICE = TextToWordPdf
