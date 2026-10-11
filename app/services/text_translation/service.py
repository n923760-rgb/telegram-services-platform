from decimal import Decimal

from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_translation.prompt import TRANSLATE
from app.services.text_translation.schema import Inputs, render, translation_schema


class TextTranslation(BaseService):
    slug = "text_translation"
    category = "text"
    name_ar = tr("text_translation_name")
    name_en = tr("text_translation_name", "en")
    description_ar = tr("text_translation_description")
    price_sar = Decimal("3.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="text_translation_input"),
            InputField(
                name="language",
                prompt_key="text_translation_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(
                name="style",
                prompt_key="translation_style",
                choices=["formal", "business", "academic", "casual"],
                choice_keys=["formal", "business", "academic", "casual"],
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
            translation_schema(values),
            values.source(),
            TRANSLATE.format(
                language={"ar": "Arabic", "en": "English"}[values.language], style=values.style
            ),
        )
        text = render(values, plan)
        artifact = self.runtime.storage.save("translation.txt", text.encode("utf-8"), "text/plain")
        return Result(text=text, artifacts=[artifact])


SERVICE = TextTranslation
