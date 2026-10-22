from decimal import Decimal

from app.core.i18n import tr, translations
from app.providers.documents.base import DocumentError
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.images_to_pdf.schema import Inputs


class ImagesToPdf(BaseService):
    version = "3"
    slug = "images_to_pdf"
    worker_requirements = ("image_pdf",)
    menu_order = 10
    category = "pdf"
    name_ar = tr("images_pdf_name")
    name_en = tr("images_pdf_name", "en")
    description_ar = tr("images_pdf_description")
    price_sar = Decimal("2.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="images",
                kind="image",
                prompt_key="images_pdf_images",
                multiple=True,
                preserve_image=True,
            ),
            InputField(
                name="page_order",
                prompt_key="images_pdf_page_order",
                required=False,
                skip_key="images_pdf_received_order",
                max_length=32,
                single_line=True,
            ),
            InputField(
                name="orientation",
                prompt_key="images_pdf_orientation",
                choices=["auto", "portrait", "landscape"],
                choice_keys=["images_pdf_auto", "images_pdf_portrait", "images_pdf_landscape"],
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
        for number in values.source_order():
            key = values.images[number - 1]
            try:
                images.append(self.runtime.storage.read(key))
            except ServiceError as error:
                if error.key in {"file_invalid", "file_expired", "not_allowed"}:
                    raise ServiceError("input_invalid") from None
                raise
            if sum(map(len, images)) > 20 * 1024 * 1024:
                raise ServiceError("input_invalid")
        try:
            if self.runtime.image_pdf is None:
                raise ServiceError("document_render_unavailable")
            pdf = await self.runtime.image_pdf.render(images, values.orientation)
        except DocumentError as error:
            raise ServiceError(error.key, transient=error.transient) from None
        artifact = self.runtime.storage.save("images.pdf", pdf, "application/pdf")
        page_order = ", ".join(map(str, values.source_order()))
        return Result(
            preview=tr("images_pdf_preview", pages=len(images), page_order=page_order),
            preview_localizations=translations(
                "images_pdf_preview", pages=len(images), page_order=page_order
            ),
            artifacts=[artifact],
        )


SERVICE = ImagesToPdf
