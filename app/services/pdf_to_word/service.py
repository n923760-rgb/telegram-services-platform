from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from app.builders import word
from app.core.i18n import tr
from app.files.pdf_content import has_image_content
from app.files.pdf_text import extract_page_text
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.pdf_to_word.prompt import PDF_TO_WORD
from app.services.pdf_to_word.schema import Inputs, WordPlan


class PdfToWord(BaseService):
    version = "3"
    slug = "pdf_to_word"
    name_ar = tr("pdf_to_word_name")
    name_en = tr("pdf_to_word_name", "en")
    description_ar = tr("pdf_to_word_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[InputField(name="pdf", kind="file", prompt_key="pdf_to_word_file")]
    )

    async def run(self, inputs):
        values = Inputs.model_validate(inputs)
        data = self.runtime.storage.read(values.pdf)
        try:
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 200:
                raise ValueError
            pages = []
            text_length = 0
            for index, page in enumerate(reader.pages, 1):
                if has_image_content(page, reader):
                    raise ServiceError("pdf_image_content")
                page_text = extract_page_text(page, limit=50000 - text_length)
                if not page_text:
                    # Do not silently omit a scanned/drawn page from a mixed PDF.
                    # Truly empty pages with no content stream may be skipped.
                    if page.get_contents() is not None:
                        raise ServiceError("pdf_text_unreadable")
                    continue
                part = f"[Page {index}]\n{page_text}"
                text_length += len(part) + (2 if pages else 0)
                if text_length > 50000:
                    raise ServiceError("pdf_text_too_long")
                pages.append(part)
        except ServiceError:
            raise
        except Exception:
            raise ServiceError("file_invalid") from None
        text = "\n\n".join(pages)
        if not pages:
            raise ServiceError("pdf_text_unreadable")
        plan = await self.runtime.ai.extract(WordPlan, text, PDF_TO_WORD)
        if plan.missing_information or plan.document is None:
            raise ServiceError("needs_information")
        content = word.build(plan.document)
        artifact = self.runtime.storage.save(
            "result.docx",
            content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        preview = tr("pdf_to_word_preview", title=plan.document.title, pages=len(reader.pages))
        return Result(preview=preview, artifacts=[artifact])


SERVICE = PdfToWord
