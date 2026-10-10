from decimal import Decimal

from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_summary.prompt import SELECT
from app.services.text_summary.schema import Inputs, render, selection_schema


class TextSummary(BaseService):
    slug = "text_summary"
    name_ar = tr("text_summary_name")
    name_en = tr("text_summary_name", "en")
    description_ar = tr("text_summary_description")
    price_sar = Decimal("3.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="text_summary_input"),
            InputField(
                name="length",
                prompt_key="text_summary_length",
                choices=["short", "standard"],
                choice_keys=["text_summary_short", "text_summary_standard"],
            ),
            InputField(
                name="language",
                prompt_key="text_summary_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return True

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        if self.runtime.ai is None:
            raise ServiceError("provider_config")
        plan = await self.runtime.ai.extract(
            selection_schema(values), values.source(), SELECT.format(limit=values.limit())
        )
        summary, report = render(values, plan)
        artifact = self.runtime.storage.save(
            "summary-source.txt", report.encode("utf-8"), "text/plain"
        )
        return Result(text=summary, artifacts=[artifact])


SERVICE = TextSummary
