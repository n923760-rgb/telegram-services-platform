from decimal import Decimal

from app.builders.schema import Document, Section
from app.builders.word import build
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.image_to_text.prompt import EXTRACT
from app.services.image_to_text.schema import Extracted, Inputs, Translation


class ImageToText(BaseService):
    slug = "image_to_text"
    name_ar = tr("ocr_name")
    name_en = tr("ocr_name", "en")
    description_ar = tr("ocr_description")
    price_sar = Decimal("3.00")
    enabled_by_default = False
    requires_ai = True
    input_schema = InputSchema(
        fields=[
            InputField(
                name="images", kind="image", prompt_key="ocr_images", multiple=True, max_items=5
            ),
            InputField(
                name="language",
                prompt_key="ocr_language",
                choices=["none", "ar", "en"],
                choice_keys=["no_translation", "arabic", "english"],
            ),
            InputField(
                name="style",
                prompt_key="translation_style",
                choices=["formal", "business", "academic", "casual"],
                choice_keys=["formal", "business", "academic", "casual"],
                when={"language": ["ar", "en"]},
            ),
        ]
    )

    async def run(self, inputs):
        values = Inputs.model_validate(inputs)
        images = [self.runtime.storage.read(key) for key in values.images]
        extracted = await self.runtime.ai.extract(Extracted, "", EXTRACT, images=images)
        if not extracted.readable or extracted.confidence < 0.7 or not extracted.text.strip():
            raise ServiceError("ocr_unclear")
        text = extracted.text.strip()
        if values.language != "none":
            translated = await self.runtime.ai.extract(
                Translation, text, language=values.language, style=values.style
            )
            text = translated.text
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
