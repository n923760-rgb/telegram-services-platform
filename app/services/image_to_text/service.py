from decimal import Decimal

from app.builders.schema import Document, Section
from app.builders.word import build
from app.core.i18n import tr
from app.providers.documents.base import DocumentError
from app.services.base import (
    BaseService,
    InputField,
    InputSchema,
    Result,
    ServiceError,
    TextFollowup,
)
from app.services.image_to_text.prompt import EXTRACT
from app.services.image_to_text.schema import Extracted, Inputs


class ImageToText(BaseService):
    version = "4"
    slug = "image_to_text"
    category = "images"
    name_ar = tr("ocr_name")
    name_en = tr("ocr_name", "en")
    description_ar = tr("ocr_description")
    price_sar = Decimal("3.00")
    enabled_by_default = False
    requires_ai = True
    text_followups = (
        TextFollowup(service="text_translation", field="text", label_key="translate_result"),
    )
    input_schema = InputSchema(
        fields=[
            InputField(
                name="images", kind="image", prompt_key="ocr_images", multiple=True, max_items=5
            ),
        ]
    )

    async def run(self, inputs):
        values = Inputs.model_validate(inputs)
        images = [self.runtime.storage.read(key) for key in values.images]
        extracted = None
        documents = getattr(self.runtime, "documents", None)
        if documents is not None and sum(map(len, images)) <= 20 * 1024 * 1024:
            try:
                recognized = await documents.recognize(images, "mixed")
                if recognized.confidence >= 0.90 and recognized.text.strip():
                    extracted = Extracted(
                        readable=True, confidence=recognized.confidence, text=recognized.text
                    )
            except DocumentError as error:
                # Invalid files, resource/security failures and other errors do not
                # authorize an outbound fallback. Both engines share one order/price.
                if error.key not in {"ocr_unclear", "local_ocr_unavailable"}:
                    raise ServiceError(error.key, transient=error.transient) from None
        if extracted is None:
            if self.runtime.ai is None:
                raise ServiceError("provider_config")
            extracted = await self.runtime.ai.extract(Extracted, "", EXTRACT, images=images)
        if not extracted.readable or extracted.confidence < 0.7 or not extracted.text.strip():
            raise ServiceError("ocr_unclear")
        text = extracted.text.strip()
        artifacts = []
        if len(text) > 3500:
            artifacts.append(
                self.runtime.storage.save("result.txt", text.encode("utf-8"), "text/plain")
            )
            paragraphs = []
            remaining = text
            while remaining:
                end = min(len(remaining), 12000)
                if end < len(remaining):
                    boundary = max(remaining.rfind(" ", 0, end), remaining.rfind("\n", 0, end))
                    if boundary > 0:
                        end = boundary
                paragraphs.append(remaining[:end])
                remaining = remaining[end:].lstrip()
            document = Document(
                title=tr("ocr_document_title"),
                sections=[Section(paragraphs=[paragraph]) for paragraph in paragraphs],
            )
            artifacts.append(
                self.runtime.storage.save(
                    "result.docx",
                    build(document),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            )
        return Result(text=text, artifacts=artifacts)


SERVICE = ImageToText
