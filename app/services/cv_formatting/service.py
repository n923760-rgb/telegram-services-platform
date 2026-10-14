from decimal import Decimal

from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, ServiceError
from app.services.cv_formatting.prompt import REFINE
from app.services.cv_formatting.schema import Inputs, document, revision_schema
from app.services.document_results import word_pdf_result


class CvFormatting(BaseService):
    slug = "cv_formatting"
    version = "5"
    worker_requirements = ("office_export",)
    menu_order = 10
    category = "professional"
    name_ar = tr("cv_name")
    name_en = tr("cv_name", "en")
    description_ar = tr("cv_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="language",
                prompt_key="cv_language",
                choices=["ar", "en", "bilingual"],
                choice_keys=["arabic", "english", "cv_bilingual"],
            ),
            InputField(
                name="cv_type",
                prompt_key="cv_type",
                required=False,
                choices=["professional", "graduate", "career_change", "academic"],
                choice_keys=[
                    "cv_type_professional",
                    "cv_type_graduate",
                    "cv_type_career_change",
                    "cv_type_academic",
                ],
            ),
            InputField(
                name="full_name", prompt_key="cv_full_name", max_length=120, single_line=True
            ),
            InputField(
                name="headline",
                prompt_key="cv_headline",
                max_length=120,
                single_line=True,
                required=False,
            ),
            InputField(name="contact", prompt_key="cv_contact", max_length=500),
            InputField(name="summary", prompt_key="cv_summary", max_length=1000, required=False),
            InputField(
                name="experience", prompt_key="cv_experience", max_length=4000, required=False
            ),
            InputField(name="education", prompt_key="cv_education", max_length=2000),
            InputField(name="skills", prompt_key="cv_skills", max_length=1500),
            InputField(name="projects", prompt_key="cv_projects", max_length=2000, required=False),
            InputField(name="languages", prompt_key="cv_languages", max_length=500, required=False),
            InputField(name="research", prompt_key="cv_research", max_length=2000, required=False),
            InputField(
                name="publications", prompt_key="cv_publications", max_length=2000, required=False
            ),
            InputField(
                name="additional", prompt_key="cv_additional", max_length=1500, required=False
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
        revision = await self.runtime.ai.extract(revision_schema(values), values.source(), REFINE)
        return await word_pdf_result(
            self.runtime,
            document(values, revision),
            filename="cv",
            preview=tr("cv_preview"),
            preview_localizations=translations("cv_preview"),
        )


SERVICE = CvFormatting
