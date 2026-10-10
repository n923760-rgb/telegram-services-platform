from decimal import Decimal

from app.builders import pptx
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_to_pptx.prompt import DECK
from app.services.text_to_pptx.schema import DeckPlan, Inputs


class TextToPptx(BaseService):
    version = "2"
    slug = "text_to_pptx"
    name_ar = tr("pptx_name")
    name_en = tr("pptx_name", "en")
    description_ar = tr("pptx_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(fields=[InputField(name="text", prompt_key="pptx_text")])

    async def run(self, inputs):
        clean = {k: v for k, v in inputs.items() if not k.startswith("__")}
        values = Inputs.model_validate(clean)
        continuation = inputs.get("__continuation")
        plan = (
            DeckPlan.model_validate(continuation)
            if continuation
            else await self.runtime.ai.extract(DeckPlan, values.text, DECK)
        )
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
