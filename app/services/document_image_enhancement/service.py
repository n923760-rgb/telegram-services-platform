import asyncio
from decimal import Decimal

from app.builders.document_image import build
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.document_image_enhancement.schema import Inputs


class DocumentImageEnhancement(BaseService):
    slug = "document_image_enhancement"
    category = "images"
    name_ar = tr("document_image_name")
    name_en = tr("document_image_name", "en")
    description_ar = tr("document_image_description")
    price_sar = Decimal("2.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="image", kind="image", prompt_key="document_image_input"),
            InputField(
                name="mode",
                prompt_key="document_image_mode",
                choices=["contrast", "grayscale"],
                choice_keys=["document_image_contrast", "document_image_grayscale"],
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        try:
            source = self.runtime.storage.read(values.image)
        except ServiceError as error:
            if error.key in {"file_invalid", "file_expired", "not_allowed"}:
                raise ServiceError("input_invalid") from None
            raise
        try:
            extension, mime, enhanced, comparison = await asyncio.to_thread(
                build, source, values.mode
            )
        except (ValueError, KeyError):
            raise ServiceError("input_invalid") from None
        artifacts = []
        try:
            for filename, data, kind in [
                ("received." + extension, source, mime),
                ("enhanced.png", enhanced, "image/png"),
                ("comparison.png", comparison, "image/png"),
            ]:
                artifacts.append(self.runtime.storage.save(filename, data, kind))
        except BaseException:
            for artifact in artifacts:
                self.runtime.storage.delete(artifact.key)
            raise
        return Result(
            artifacts=artifacts,
            preview=tr("document_image_result"),
            preview_localizations=translations("document_image_result"),
        )


SERVICE = DocumentImageEnhancement
