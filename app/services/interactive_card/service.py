import asyncio
import json
from decimal import Decimal

from pydantic import ValidationError

from app.builders.interactive_card import build
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.interactive_card.prompt import PRESENT
from app.services.interactive_card.schema import Inputs, presentation_schema


class InteractiveCard(BaseService):
    slug = "interactive_card"
    version = "2"
    category = "professional"
    menu_order = 30
    name_ar = tr("card_name")
    name_en = tr("card_name", "en")
    description_ar = tr("card_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    optional_ai = True
    ai_intake_choices = {"mode": ("smart",)}
    enabled_by_default = False
    worker_requirements = ("pdf_font",)
    input_schema = InputSchema(
        fields=[
            InputField(
                name="mode",
                prompt_key="card_arrangement",
                choices=["smart", "direct"],
                choice_keys=["card_smart", "card_direct"],
            ),
            InputField(
                name="language",
                prompt_key="card_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(name="name", prompt_key="card_person", single_line=True, max_length=48),
            InputField(
                name="subtitle",
                prompt_key="card_subtitle",
                single_line=True,
                max_length=60,
                required=False,
            ),
            InputField(name="links", prompt_key="card_links", max_length=2400),
            InputField(name="profile", prompt_key="card_profile", max_length=1000, required=False),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        return Inputs.parse(inputs).mode == "smart"

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        plan = None
        if values.mode == "smart":
            if self.runtime.ai is None:
                raise ServiceError("provider_config")
            schema = presentation_schema(values)
            source = json.dumps(
                {
                    "language": values.language,
                    "name": values.name,
                    "subtitle": values.subtitle,
                    "profile": values.profile,
                    "buttons": [
                        {"index": i, "label": label}
                        for i, (label, _) in enumerate(values.entries())
                    ],
                },
                ensure_ascii=False,
            )
            try:
                result = await self.runtime.ai.extract(schema, source, PRESENT)
                plan = schema.model_validate(result.model_dump(mode="json"))
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
        content = await asyncio.to_thread(build, values, plan)
        artifact = self.runtime.storage.save("business-card.pdf", content, "application/pdf")
        return Result(
            preview=tr("card_preview", values.language),
            preview_localizations=translations("card_preview"),
            artifacts=[artifact],
        )


SERVICE = InteractiveCard
