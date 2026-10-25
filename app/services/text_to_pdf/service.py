from decimal import Decimal

from pydantic import ValidationError

from app.builders import pdf
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.document_fidelity import source_document_schema
from app.services.text_to_pdf.prompt import PDF
from app.services.text_to_pdf.schema import Inputs, PdfPlan


class TextToPdf(BaseService):
    version = "7"
    slug = "text_to_pdf"
    worker_requirements = ("pdf_font",)
    menu_order = 20
    category = "documents"
    name_ar = tr("pdf_name")
    name_en = tr("pdf_name", "en")
    description_ar = tr("pdf_description")
    price_sar = Decimal("5.00")
    requires_ai = False  # Direct PDF can be enabled without a provider.
    optional_ai = True
    ai_intake_choices = {"mode": ("smart",)}
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="mode",
                required=False,
                legacy_only=True,
                prompt_key="document_mode",
                choices=["direct", "smart"],
                choice_keys=["document_direct", "document_smart"],
            ),
            InputField(name="text", prompt_key="pdf_text"),
            InputField(
                name="title",
                legacy_only=True,
                prompt_key="document_title",
                max_length=200,
                required=False,
                skip_key="document_no_title",
                single_line=True,
                when={"mode": ["direct"]},
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        return Inputs.parse(inputs).mode != "direct" and not inputs.get("__continuation")

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        continuation = inputs.get("__continuation")
        schema = source_document_schema(PdfPlan, values.text)
        if values.mode != "direct" and not continuation and self.runtime.ai is None:
            raise ServiceError("provider_config")
        try:
            plan = (
                PdfPlan(document=values.document())
                if values.mode == "direct"
                else schema.model_validate(continuation)
                if continuation
                else await self.runtime.ai.extract(schema, values.text, PDF)
            )
            if values.mode != "direct":
                plan = schema.model_validate(plan.model_dump(mode="json"))
        except (ValidationError, ValueError):
            raise ServiceError("provider_invalid") from None
        if plan.missing_information:
            raise ServiceError("needs_information")
        reviews = {}
        for lang in ("ar", "en"):
            preview = (
                (
                    tr("document_direct_preview", lang, title=values.title)
                    if values.title
                    else tr("document_direct_no_title_preview", lang)
                )
                if values.mode == "direct"
                else tr(
                    "pdf_preview",
                    lang,
                    title=plan.document.title,
                    sections=len(plan.document.sections),
                )
            )
            preview = preview[:1400]
            reviews[lang] = preview
        preview = reviews["ar"]
        if plan.ambiguous and not continuation:
            return Result(
                preview=tr("ambiguous_preview", question=plan.question, preview=preview),
                preview_localizations={
                    lang: tr("ambiguous_preview", lang, question=plan.question, preview=review)
                    for lang, review in reviews.items()
                },
                needs_confirmation=True,
                continuation=plan.model_dump(mode="json"),
            )
        content = (
            pdf.build(plan.document, include_title=False)
            if values.mode == "direct" and values.title is None
            else pdf.build(plan.document)
        )
        artifact = self.runtime.storage.save("result.pdf", content, "application/pdf")
        return Result(preview=preview, preview_localizations=reviews, artifacts=[artifact])


SERVICE = TextToPdf
