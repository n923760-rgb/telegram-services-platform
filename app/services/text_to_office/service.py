from decimal import Decimal

from app.builders import excel, word
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.text_to_office.prompt import EXCEL, WORD
from app.services.text_to_office.schema import ExcelPlan, Inputs, WordPlan


class TextToOffice(BaseService):
    version = "5"
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
            WordPlan(document=values.document().model_dump())
            if values.mode == "direct"
            else schema.model_validate(continuation)
            if continuation
            else await self.runtime.ai.extract(
                schema, values.text, WORD if values.target == "word" else EXCEL
            )
        )
        if plan.missing_information:
            raise ServiceError("needs_information")
        reviews = {}
        for lang in ("ar", "en"):
            if values.mode == "direct":
                preview = (
                    tr("document_direct_preview", lang, title=values.title)
                    if values.title
                    else tr("document_direct_no_title_preview", lang)
                )
            elif values.target == "word":
                preview = tr(
                    "word_professional_preview",
                    lang,
                    title=plan.document.title,
                    headings="، ".join(
                        s.heading or tr("paragraphs", lang) for s in plan.document.sections[:5]
                    ),
                    tables=sum(len(s.tables) for s in plan.document.sections),
                )
            else:
                preview = tr(
                    "excel_preview",
                    lang,
                    columns="، ".join(plan.table.columns[:8]),
                    rows=len(plan.table.rows),
                )
                missing = sum(cell is None for row in plan.table.rows for cell in row)
                unique = {
                    tuple((type(cell).__name__, cell) for cell in row) for row in plan.table.rows
                }
                repeated = len(plan.table.rows) - len(unique)
                if missing or repeated:
                    preview += "\n" + tr(
                        "excel_data_notes", lang, missing=missing, repeated=repeated
                    )
                preview += "\n" + tr("excel_usage", lang)
            preview = preview[:1400]
            reviews[lang] = preview
        preview = reviews["ar"]
        if plan.ambiguous and not continuation:
            return Result(
                preview=tr("ambiguous_preview", question=plan.question, preview=preview),
                preview_localizations={
                    lang: tr("ambiguous_preview", lang, question=plan.question, preview=review)
                    for lang, review in reviews.items()
                },
                needs_confirmation=True,
                continuation=plan.model_dump(mode="json"),
            )
        if values.target == "word":
            content = (
                word.build(plan.document, include_title=False)
                if values.mode == "direct" and values.title is None
                else word.build(
                    plan.document,
                    format_dates=values.mode != "direct",
                    professional_template=values.mode != "direct",
                )
            )
            name = "result.docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            content = excel.build(plan.table)
            name = "result.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        artifact = self.runtime.storage.save(name, content, mime)
        return Result(preview=preview, preview_localizations=reviews, artifacts=[artifact])


SERVICE = TextToOffice
