from decimal import Decimal

from app.builders import excel, word
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_to_office.prompt import EXCEL, WORD
from app.services.text_to_office.schema import ExcelPlan, Inputs, WordPlan


class TextToOffice(BaseService):
    slug = "text_to_office"
    name_ar = tr("office_name")
    name_en = tr("office_name", "en")
    description_ar = tr("office_description")
    price_sar = Decimal("5.00")
    requires_ai = True
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
        ]
    )

    async def run(self, inputs):
        clean = {k: v for k, v in inputs.items() if not k.startswith("__")}
        values = Inputs.model_validate(clean)
        schema = WordPlan if values.target == "word" else ExcelPlan
        continuation = inputs.get("__continuation")
        plan = (
            schema.model_validate(continuation)
            if continuation
            else await self.runtime.ai.extract(
                schema, values.text, WORD if values.target == "word" else EXCEL
            )
        )
        if plan.missing_information:
            raise ServiceError("needs_information")
        if values.target == "word":
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
            content = word.build(plan.document)
            name = "result.docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            content = excel.build(plan.table)
            name = "result.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        artifact = self.runtime.storage.save(name, content, mime)
        return Result(preview=preview, artifacts=[artifact])


SERVICE = TextToOffice
