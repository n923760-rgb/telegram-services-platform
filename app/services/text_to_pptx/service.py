from decimal import Decimal

from pydantic import ValidationError

from app.builders import pptx
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.protected_values import ProtectedValues
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.text_to_pptx.prompt import DECK, REFERENCE_CONTEXT, SLIDE_COUNT
from app.services.text_to_pptx.schema import Inputs, source_plan_schema


class TextToPptx(BaseService):
    version = "7"
    slug = "text_to_pptx"
    menu_order = 40
    category = "documents"
    name_ar = tr("pptx_name")
    name_en = tr("pptx_name", "en")
    description_ar = tr("pptx_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="slide_count",
                prompt_key="pptx_slide_count",
                required=False,
                max_length=4,
                single_line=True,
                skip_key="pptx_slide_count_auto",
            ),
            InputField(name="text", prompt_key="pptx_text"),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return "__continuation" not in inputs

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        protected = ProtectedValues(values.text, CONTACT_TOKEN)
        schema = source_plan_schema(values.text, values.slide_count, protected=protected)
        continuation = inputs.get("__continuation")
        if "__continuation" in inputs:
            try:
                plan = schema.model_validate(continuation)
            except ValidationError:
                raise ServiceError("provider_invalid") from None
        else:
            if self.runtime.ai is None:
                raise ServiceError("provider_config")
            prompt = DECK + protected.instruction()
            if protected.values:
                prompt += "\n" + REFERENCE_CONTEXT
            if values.slide_count is not None:
                prompt += "\n\n" + SLIDE_COUNT.format(count=values.slide_count)
            plan = await self.runtime.ai.extract(schema, protected.request(), prompt)
            try:
                plan = schema.model_validate(plan.model_dump(mode="json"))
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
        if plan.missing_information:
            raise ServiceError("needs_information")
        reviews = {}
        for lang in ("ar", "en"):
            preview = tr(
                "pptx_preview",
                lang,
                slides=len(plan.deck.slides),
                title=plan.deck.slides[0].title,
            )
            tables = sum(slide.table is not None for slide in plan.deck.slides)
            if tables:
                preview += "\n" + tr("pptx_tables_preview", lang, tables=tables)
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
        content = pptx.build(plan.deck)
        artifact = self.runtime.storage.save(
            "result.pptx",
            content,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        return Result(preview=preview, preview_localizations=reviews, artifacts=[artifact])


SERVICE = TextToPptx
