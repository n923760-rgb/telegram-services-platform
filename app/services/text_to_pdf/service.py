from decimal import Decimal

from app.builders import pdf
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_to_pdf.prompt import PDF
from app.services.text_to_pdf.schema import Inputs, PdfPlan


class TextToPdf(BaseService):
    version = "2"
    slug = "text_to_pdf"
    name_ar = tr("pdf_name")
    name_en = tr("pdf_name", "en")
    description_ar = tr("pdf_description")
    price_sar = Decimal("5.00")
    requires_ai = False  # Direct PDF can be enabled without a provider.
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="pdf_text"),
            InputField(
                name="mode",
                prompt_key="document_mode",
                choices=["direct", "smart"],
                choice_keys=["document_direct", "document_smart"],
            ),
            InputField(
                name="title", prompt_key="document_title", max_length=200, when={"mode": ["direct"]}
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        return Inputs.parse(inputs).mode != "direct" and not inputs.get("__continuation")

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        continuation = inputs.get("__continuation")
        plan = (
            PdfPlan(document=values.document())
            if values.mode == "direct"
            else PdfPlan.model_validate(continuation)
            if continuation
            else await self.runtime.ai.extract(PdfPlan, values.text, PDF)
        )
        if plan.missing_information:
            raise ServiceError("needs_information")
        preview = (
            tr("document_direct_preview", title=plan.document.title)
            if values.mode == "direct"
            else tr(
                "pdf_preview",
                title=plan.document.title,
                sections=len(plan.document.sections),
            )
        )
        preview = preview[:1400]
        if plan.ambiguous and not continuation:
            return Result(
                preview=tr("ambiguous_preview", question=plan.question, preview=preview),
                needs_confirmation=True,
                continuation=plan.model_dump(mode="json"),
            )
        content = pdf.build(plan.document)
        artifact = self.runtime.storage.save("result.pdf", content, "application/pdf")
        return Result(preview=preview, artifacts=[artifact])


SERVICE = TextToPdf
