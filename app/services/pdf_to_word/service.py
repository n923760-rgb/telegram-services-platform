from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from app.builders import word
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.pdf_to_word.prompt import PDF_TO_WORD
from app.services.pdf_to_word.schema import Inputs, WordPlan


class PdfToWord(BaseService):
    slug = "pdf_to_word"
    name_ar = tr("pdf_to_word_name")
    name_en = tr("pdf_to_word_name", "en")
    description_ar = tr("pdf_to_word_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(fields=[InputField(name="pdf", kind="file", prompt_key="pdf_to_word_file")])

    async def run(self, inputs):
        values = Inputs.model_validate(inputs)
        data = self.runtime.storage.read(values.pdf)
        try:
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 200:
                raise ValueError
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
        except Exception:
            raise ServiceError("file_invalid") from None
        text = "\n\n".join(f"[Page {i}]\n{page}" for i, page in enumerate(pages, 1) if page)
        if len(text.strip()) < 20:
            raise ServiceError("pdf_text_unreadable")
        if len(text) > 50000:
            raise ServiceError("pdf_text_too_long")
        plan = await self.runtime.ai.extract(WordPlan, text, PDF_TO_WORD)
        if plan.missing_information or plan.document is None:
            raise ServiceError("needs_information")
        content = word.build(plan.document)
        artifact = self.runtime.storage.save(
            "result.docx", content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        preview = tr("pdf_to_word_preview", title=plan.document.title, pages=len(reader.pages))
        return Result(preview=preview, artifacts=[artifact])


SERVICE = PdfToWord
