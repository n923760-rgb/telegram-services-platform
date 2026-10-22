import asyncio
from decimal import Decimal

from app.builders.document_image import build
from app.core.i18n import tr, translations
from app.files.validation import image
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.document_image_enhancement.prompt import ASSESS
from app.services.document_image_enhancement.schema import Assessment, Inputs


class DocumentImageEnhancement(BaseService):
    version = "4"
    slug = "document_image_enhancement"
    worker_requirements = ("document_images",)
    menu_order = 20
    category = "images"
    name_ar = tr("document_image_name")
    name_en = tr("document_image_name", "en")
    description_ar = tr("document_image_description")
    price_sar = Decimal("2.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="image", kind="image", prompt_key="document_image_input", preserve_image=True
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return True

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        try:
            source = self.runtime.storage.read(values.image)
        except ServiceError as error:
            if error.key in {"file_invalid", "file_expired", "not_allowed"}:
                raise ServiceError("input_invalid") from None
            raise
        try:
            extension, mime, contrast, contrast_comparison = await asyncio.to_thread(build, source)
            _, _, sharpen, sharpen_comparison = await asyncio.to_thread(build, source, "sharpen")
        except (ValueError, KeyError):
            raise ServiceError("input_invalid") from None
        if self.runtime.ai is None:
            raise ServiceError("provider_config")
        evidence = [
            await asyncio.to_thread(image, data, 10 * 1024 * 1024, max_side=2048)
            for data in (source, contrast, sharpen)
        ]
        verdict = await self.runtime.ai.extract(Assessment, "", ASSESS, images=evidence)
        if verdict.choice == "none":
            raise ServiceError("enhancement_not_improved")
        enhanced, comparison = (
            (contrast, contrast_comparison)
            if verdict.choice == "contrast"
            else (sharpen, sharpen_comparison)
        )
        artifacts = []
        try:
            for filename, data, kind in [
                ("enhanced.png", enhanced, "image/png"),
                ("comparison.png", comparison, "image/png"),
                ("received." + extension, source, mime),
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
