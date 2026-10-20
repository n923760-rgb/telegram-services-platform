from decimal import Decimal

from pydantic import ValidationError

from app.builders import word
from app.builders.excel_source import build as source_workbook
from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.document_fidelity import CONTACT_TOKEN, source_document_schema
from app.services.protected_values import ProtectedValues
from app.services.text_to_office.excel_source import source_excel_schema, source_json
from app.services.text_to_office.prompt import EXCEL, WORD
from app.services.text_to_office.schema import Inputs, WordPlan


class TextToOffice(BaseService):
    version = "8"
    slug = "text_to_office"
    menu_order = 10
    category = "documents"
    name_ar = tr("office_name")
    name_en = tr("office_name", "en")
    description_ar = tr("office_description")
    price_sar = Decimal("5.00")
    requires_ai = False  # Direct Word can be enabled without a provider.
    optional_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="target",
                prompt_key="office_target",
                choices=["word", "excel"],
                choice_keys=["word", "excel"],
            ),
            InputField(
                name="mode",
                prompt_key="office_word_mode",
                choices=["direct", "smart"],
                choice_keys=["office_word_direct", "office_word_smart"],
                when={"target": ["word"]},
            ),
            InputField(name="text", prompt_key="office_text"),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        return Inputs.parse(inputs).mode != "direct" and not inputs.get("__continuation")

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        protected = ProtectedValues(values.text, CONTACT_TOKEN) if values.target == "word" else None
        schema = (
            source_document_schema(WordPlan, values.text, protected=protected)
            if values.target == "word"
            else source_excel_schema(values)
        )
        continuation = inputs.get("__continuation")
        if values.mode != "direct" and not continuation and self.runtime.ai is None:
            raise ServiceError("provider_config")
        try:
            plan = (
                WordPlan(document=values.document().model_dump())
                if values.mode == "direct"
                else schema.model_validate(continuation)
                if continuation
                else await self.runtime.ai.extract(
                    schema,
                    protected.request() if protected is not None else source_json(values),
                    WORD + protected.instruction() if protected is not None else EXCEL,
                )
            )
        except ValidationError:
            raise ServiceError("provider_invalid") from None
        if values.mode != "direct":
            try:
                plan = schema.model_validate(plan.model_dump(mode="json"))
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
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
                preview = (
                    tr("excel_source_review", lang, context=len(plan.context_ids)) + "\n" + preview
                )
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
            content = source_workbook(
                plan.table,
                values.lines(),
                [row.source_id for row in plan.evidence],
                [row.quotes for row in plan.evidence],
            )
            name = "result.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        artifact = self.runtime.storage.save(name, content, mime)
        return Result(preview=preview, preview_localizations=reviews, artifacts=[artifact])


SERVICE = TextToOffice
