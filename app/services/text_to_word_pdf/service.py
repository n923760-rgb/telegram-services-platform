from decimal import Decimal

from app.builders.word_schema import WordDocument
from app.core.i18n import tr
from app.providers.documents.base import DocumentError
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
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
        if self.runtime.renderer is None:
            raise ServiceError("document_render_unavailable")
        try:
            result = await self.runtime.renderer.word_pdf(
                WordDocument.model_validate(values.document().model_dump()),
                include_title=values.title is not None,
            )
        except DocumentError as error:
            if error.key == "document_render_limit":
                raise ServiceError("input_invalid") from None
            raise ServiceError(error.key, transient=error.transient) from None
        artifacts = []
        try:
            artifacts.append(
                self.runtime.storage.save(
                    "result.docx",
                    result.docx,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            )
            artifacts.append(self.runtime.storage.save("result.pdf", result.pdf, "application/pdf"))
        except BaseException:
            for artifact in artifacts:
                self.runtime.storage.delete(artifact.key)
            raise
        return Result(preview=tr("word_pdf_preview"), artifacts=artifacts)


SERVICE = TextToWordPdf
