from decimal import Decimal

from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, ServiceError
from app.services.cv_formatting.import_cv import EditRequest, import_cv
from app.services.cv_formatting.prompt import REFINE
from app.services.cv_formatting.schema import Inputs, document, revision_schema
from app.services.document_results import word_pdf_result


def _create_field(**kwargs):
    return InputField(when={"mode": [None, "create"]}, **kwargs)


def _request(inputs):
    if inputs.get("mode") in ("edit_pdf", "edit_text"):
        return EditRequest.parse(inputs)
    return Inputs.parse(inputs)


class CvFormatting(BaseService):
    slug = "cv_formatting"
    version = "8"
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
                name="mode",
                prompt_key="cv_mode",
                required=False,
                choices=["create", "edit_pdf", "edit_text"],
                choice_keys=["cv_create", "cv_edit_pdf", "cv_edit_text"],
            ),
            InputField(
                name="language",
                prompt_key="cv_language",
                choices=["ar", "en", "bilingual_split", "bilingual"],
                choice_keys=["arabic", "english", "cv_bilingual_split", "cv_bilingual"],
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
                name="source_pdf",
                kind="file",
                prompt_key="cv_source_pdf",
                when={"mode": ["edit_pdf"]},
            ),
            InputField(
                name="source_text",
                prompt_key="cv_source_text",
                max_length=9000,
                when={"mode": ["edit_text"]},
            ),
            _create_field(
                name="full_name", prompt_key="cv_full_name", max_length=120, single_line=True
            ),
            _create_field(
                name="headline",
                prompt_key="cv_headline",
                max_length=120,
                single_line=True,
                required=False,
            ),
            _create_field(name="contact", prompt_key="cv_contact", max_length=500),
            _create_field(name="summary", prompt_key="cv_summary", max_length=1000, required=False),
            _create_field(
                name="experience", prompt_key="cv_experience", max_length=4000, required=False
            ),
            _create_field(name="education", prompt_key="cv_education", max_length=2000),
            _create_field(name="skills", prompt_key="cv_skills", max_length=1500),
            _create_field(
                name="projects", prompt_key="cv_projects", max_length=2000, required=False
            ),
            _create_field(
                name="languages", prompt_key="cv_languages", max_length=500, required=False
            ),
            _create_field(
                name="research", prompt_key="cv_research", max_length=2000, required=False
            ),
            _create_field(
                name="publications", prompt_key="cv_publications", max_length=2000, required=False
            ),
            _create_field(
                name="additional", prompt_key="cv_additional", max_length=1500, required=False
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        _request(inputs)
        return True

    async def run(self, inputs):
        values = _request(inputs)
        if self.runtime.ai is None:
            raise ServiceError("provider_config")
        if isinstance(values, EditRequest):
            values = await import_cv(self.runtime, values)
        revision = await self.runtime.ai.extract(revision_schema(values), values.source(), REFINE)
        split = values.language == "bilingual_split"
        preview_key = "cv_preview_split" if split else "cv_preview"
        return await word_pdf_result(
            self.runtime,
            document(values, revision),
            filename="cv",
            preview=tr(preview_key),
            preview_localizations=translations(preview_key),
            single_page_error="cv_split_too_long" if split else None,
        )


SERVICE = CvFormatting
