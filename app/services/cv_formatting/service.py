from decimal import Decimal

from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema
from app.services.cv_formatting.schema import Inputs
from app.services.document_results import word_pdf_result


class CvFormatting(BaseService):
    slug = "cv_formatting"
    name_ar = tr("cv_name")
    name_en = tr("cv_name", "en")
    description_ar = tr("cv_description")
    price_sar = Decimal("5.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="language",
                prompt_key="cv_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(
                name="full_name", prompt_key="cv_full_name", max_length=120, single_line=True
            ),
            InputField(name="contact", prompt_key="cv_contact", max_length=500),
            InputField(name="summary", prompt_key="cv_summary", max_length=1000, required=False),
            InputField(
                name="experience", prompt_key="cv_experience", max_length=4000, required=False
            ),
            InputField(
                name="education", prompt_key="cv_education", max_length=2000, required=False
            ),
            InputField(name="skills", prompt_key="cv_skills", max_length=1500),
            InputField(
                name="additional", prompt_key="cv_additional", max_length=1500, required=False
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        return await word_pdf_result(
            self.runtime, values.document(), filename="cv", preview=tr("cv_preview")
        )


SERVICE = CvFormatting
