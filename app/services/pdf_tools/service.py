from decimal import Decimal

from app.builders.pdf_tools import PdfToolError, build
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.pdf_tools.schema import Inputs


class PdfTools(BaseService):
    slug = "pdf_tools"
    version = "1"
    name_ar = tr("pdf_tools_name")
    name_en = tr("pdf_tools_name", "en")
    description_ar = tr("pdf_tools_description")
    price_sar = Decimal("2.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="operation",
                prompt_key="pdf_tools_operation",
                choices=["merge", "extract"],
                choice_keys=["pdf_tools_merge", "pdf_tools_extract"],
            ),
            InputField(name="files", kind="file", prompt_key="pdf_tools_files", multiple=True),
            InputField(
                name="pages",
                prompt_key="pdf_tools_pages",
                max_length=200,
                single_line=True,
                when={"operation": ["extract"]},
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)  # Validate cross-field requirements before reserving credit.
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        data = []
        for key in values.files:
            data.append(self.runtime.storage.read(key))
            if sum(map(len, data)) > 20 * 1024 * 1024:
                raise ServiceError("pdf_tools_limit")
        try:
            content = build(data, operation=values.operation, pages=values.pages)
        except PdfToolError as error:
            raise ServiceError(error.key) from None
        artifact = self.runtime.storage.save("result.pdf", content, "application/pdf")
        return Result(preview=tr("pdf_tools_preview"), artifacts=[artifact])


SERVICE = PdfTools
