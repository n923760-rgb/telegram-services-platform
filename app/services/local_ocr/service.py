from decimal import Decimal

from app.core.i18n import tr
from app.providers.documents.base import DocumentError
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.local_ocr.schema import Inputs


class LocalOcr(BaseService):
    slug = "local_ocr"
    name_ar = tr("local_ocr_name")
    name_en = tr("local_ocr_name", "en")
    description_ar = tr("local_ocr_description")
    price_sar = Decimal("2.00")
    enabled_by_default = False
    requires_ai = False
    input_schema = InputSchema(
        fields=[
            InputField(name="images", kind="image", prompt_key="local_ocr_images", multiple=True),
            InputField(
                name="language",
                prompt_key="local_ocr_language",
                choices=["ar", "en", "mixed"],
                choice_keys=["arabic", "english", "local_ocr_mixed"],
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        images = []
        for key in values.images:
            try:
                images.append(self.runtime.storage.read(key))
            except ServiceError as error:
                if error.key in {"file_invalid", "file_expired", "not_allowed"}:
                    raise ServiceError("input_invalid") from None
                raise
            if sum(map(len, images)) > 20 * 1024 * 1024:
                raise ServiceError("input_invalid")
        if self.runtime.documents is None:
            raise ServiceError("local_ocr_unavailable")
        try:
            recognized = await self.runtime.documents.recognize(images, values.language)
        except DocumentError as error:
            raise ServiceError(error.key, transient=error.transient) from None
        except ServiceError as error:
            if error.key == "file_invalid":
                raise ServiceError("input_invalid") from None
            raise
        artifacts = []
        if len(recognized.text) > 3500:
            artifacts.append(
                self.runtime.storage.save(
                    "result.txt", recognized.text.encode("utf-8"), "text/plain"
                )
            )
        return Result(text=recognized.text, preview=tr("local_ocr_preview"), artifacts=artifacts)


SERVICE = LocalOcr
