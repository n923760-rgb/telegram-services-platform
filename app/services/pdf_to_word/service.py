from decimal import Decimal
from io import BytesIO

from pydantic import ValidationError
from pypdf import PdfReader

from app.builders import word
from app.core.i18n import tr, translations
from app.files.pdf_content import has_image_content
from app.files.pdf_text import extract_page_text
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.pdf_to_word.prompt import PDF_TO_WORD
from app.services.pdf_to_word.schema import Inputs, source_plan_schema


class PdfToWord(BaseService):
    version = "6"
    slug = "pdf_to_word"
    menu_order = 20
    category = "pdf"
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
            # Text extraction cannot preserve interactive values or signatures.
            # Even an empty declaration is unsupported, not proof of plain text.
            root = reader.trailer["/Root"]
            if root.get("/AcroForm") is not None or root.get("/Perms") is not None:
                raise ServiceError("pdf_word_form")
            pages = []
            sources = []
            text_length = 0
            for index, page in enumerate(reader.pages, 1):
                annotations = page.get("/Annots")
                if annotations is not None and any(
                    annotation.get_object()["/Subtype"] == "/Widget"
                    for annotation in annotations.get_object()
                ):
                    raise ServiceError("pdf_word_form")
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
                sources.append(page_text)
        except ServiceError:
            raise
        except Exception:
            raise ServiceError("file_invalid") from None
        text = "\n\n".join(pages)
        if not pages:
            raise ServiceError("pdf_text_unreadable")
        # Synthetic page markers guide the model but are not customer facts.
        schema = source_plan_schema("\n\n".join(sources))
        plan = await self.runtime.ai.extract(schema, text, PDF_TO_WORD)
        try:
            # Recheck injected providers too, before any builder/storage writes.
            plan = schema.model_validate(plan.model_dump(mode="json"))
        except (ValidationError, ValueError):
            raise ServiceError("provider_invalid") from None
        content = word.build(plan.document)
        artifact = self.runtime.storage.save(
            "result.docx",
            content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        preview = tr("pdf_to_word_preview", title=plan.document.title, pages=len(reader.pages))
        return Result(
            preview=preview,
            preview_localizations=translations(
                "pdf_to_word_preview", title=plan.document.title, pages=len(reader.pages)
            ),
            artifacts=[artifact],
        )


SERVICE = PdfToWord
