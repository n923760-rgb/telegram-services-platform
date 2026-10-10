from decimal import Decimal

from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_editing.prompt import EDIT
from app.services.text_editing.schema import Inputs, render, revision_schema


class TextEditing(BaseService):
    slug = "text_editing"
    name_ar = tr("text_editing_name")
    name_en = tr("text_editing_name", "en")
    description_ar = tr("text_editing_description")
    price_sar = Decimal("3.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="text_editing_input"),
            InputField(
                name="mode",
                prompt_key="text_editing_mode",
                choices=["proofread", "rewrite"],
                choice_keys=["text_editing_proofread", "text_editing_rewrite"],
            ),
            InputField(
                name="tone",
                prompt_key="text_editing_tone",
                choices=["formal", "business", "casual"],
                choice_keys=["formal", "business", "casual"],
                when={"mode": ["rewrite"]},
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
            revision_schema(values),
            values.source(),
            EDIT.format(mode=values.mode, tone=values.tone),
        )
        text = render(values, plan)
        artifact = self.runtime.storage.save("revision.txt", text.encode("utf-8"), "text/plain")
        return Result(text=text, artifacts=[artifact])


SERVICE = TextEditing
