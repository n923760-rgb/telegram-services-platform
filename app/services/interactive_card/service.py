import asyncio
from decimal import Decimal

from app.builders.interactive_card import build
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result
from app.services.interactive_card.schema import Inputs


class InteractiveCard(BaseService):
    slug = "interactive_card"
    version = "1"
    category = "professional"
    menu_order = 30
    name_ar = tr("card_name")
    name_en = tr("card_name", "en")
    description_ar = tr("card_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    enabled_by_default = False
    worker_requirements = ("pdf_font",)
    input_schema = InputSchema(
        fields=[
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
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        content = await asyncio.to_thread(build, values)
        artifact = self.runtime.storage.save("business-card.pdf", content, "application/pdf")
        return Result(
            preview=tr("card_preview", values.language),
            preview_localizations=translations("card_preview"),
            artifacts=[artifact],
        )


SERVICE = InteractiveCard
