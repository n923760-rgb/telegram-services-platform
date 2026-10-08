from decimal import Decimal

from app.builders import excel, word
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_to_office.prompt import EXCEL, WORD
from app.services.text_to_office.schema import ExcelPlan, Inputs, WordPlan


class TextToOffice(BaseService):
    version = "3"
    slug = "text_to_office"
    name_ar = tr("office_name")
    name_en = tr("office_name", "en")
    description_ar = tr("office_description")
    price_sar = Decimal("5.00")
    requires_ai = False  # Direct Word can be enabled without a provider.
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="text", prompt_key="office_text"),
            InputField(
                name="target",
                prompt_key="office_target",
                choices=["word", "excel"],
                choice_keys=["word", "excel"],
            ),
            InputField(
                name="mode",
                prompt_key="document_mode",
                choices=["direct", "smart"],
                choice_keys=["document_direct", "document_smart"],
                when={"target": ["word"]},
            ),
            InputField(
                name="title",
                prompt_key="document_title",
                max_length=200,
                required=False,
                skip_key="document_no_title",
                single_line=True,
                when={"target": ["word"], "mode": ["direct"]},
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        return Inputs.parse(inputs).mode != "direct" and not inputs.get("__continuation")

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        schema = WordPlan if values.target == "word" else ExcelPlan
        continuation = inputs.get("__continuation")
        plan = (
            WordPlan(document=values.document())
            if values.mode == "direct"
            else schema.model_validate(continuation)
            if continuation
            else await self.runtime.ai.extract(
                schema, values.text, WORD if values.target == "word" else EXCEL
            )
        )
        if plan.missing_information:
            raise ServiceError("needs_information")
        if values.mode == "direct":
            preview = (
                tr("document_direct_preview", title=values.title)
                if values.title
                else tr("document_direct_no_title_preview")
            )
        elif values.target == "word":
            preview = tr(
                "word_preview",
                title=plan.document.title,
                headings="، ".join(
                    s.heading or tr("paragraphs") for s in plan.document.sections[:5]
                ),
            )
        else:
            preview = tr(
                "excel_preview",
                columns="، ".join(plan.table.columns[:8]),
                rows=len(plan.table.rows),
            )
        preview = preview[:1400]
        if plan.ambiguous and not continuation:
            return Result(
                preview=tr("ambiguous_preview", question=plan.question, preview=preview),
                needs_confirmation=True,
                continuation=plan.model_dump(mode="json"),
            )
        if values.target == "word":
            content = (
                word.build(plan.document, include_title=False)
                if values.mode == "direct" and values.title is None
                else word.build(plan.document)
            )
            name = "result.docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            content = excel.build(plan.table)
            name = "result.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        artifact = self.runtime.storage.save(name, content, mime)
        return Result(preview=preview, artifacts=[artifact])


SERVICE = TextToOffice
