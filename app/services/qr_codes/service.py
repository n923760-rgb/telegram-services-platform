import asyncio
from decimal import Decimal

from app.builders.qr_codes import build
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result
from app.services.qr_codes.schema import Inputs


class QrCodes(BaseService):
    slug = "qr_codes"
    version = "1"
    category = "professional"
    menu_order = 40
    name_ar = tr("qr_name")
    name_en = tr("qr_name", "en")
    description_ar = tr("qr_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    enabled_by_default = False
    worker_requirements = ("pdf_font",)
    input_schema = InputSchema(
        fields=[
            InputField(
                name="language",
                prompt_key="qr_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(name="entries", prompt_key="qr_entries", max_length=10000),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        content = await asyncio.to_thread(build, values)
        artifact = self.runtime.storage.save("qr-codes.pdf", content, "application/pdf")
        return Result(
            preview=tr("qr_preview", values.language),
            preview_localizations=translations("qr_preview"),
            artifacts=[artifact],
        )


SERVICE = QrCodes
