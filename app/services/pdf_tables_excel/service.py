from decimal import Decimal

from pydantic import ValidationError

from app.builders.pdf_tables import build
from app.core.i18n import tr
from app.providers.documents.base import DocumentError
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.pdf_tables_excel.prompt import LABELS
from app.services.pdf_tables_excel.schema import (
    Inputs,
    Prepared,
    ai_source,
    direct_labels,
    labels_schema,
    source_labels,
)


class PdfTablesExcel(BaseService):
    version = "7"
    slug = "pdf_tables_excel"
    worker_requirements = ("pdf_tables",)
    menu_order = 20
    category = "data"
    name_ar = tr("pdf_tables_name")
    name_en = tr("pdf_tables_name", "en")
    description_ar = tr("pdf_tables_description")
    price_sar = Decimal("5.00")
    requires_ai = False
    optional_ai = True
    ai_intake_choices = {"mode": ("labels",)}
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="mode",
                prompt_key="pdf_tables_mode",
                choices=["direct", "source", "labels"],
                choice_keys=["pdf_tables_direct", "pdf_tables_source_headers", "pdf_tables_labels"],
            ),
            InputField(name="pdf", kind="file", prompt_key="pdf_tables_file"),
            InputField(
                name="language",
                prompt_key="pdf_tables_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(
                name="arabic_order",
                prompt_key="pdf_tables_arabic_order",
                choices=["visual"],
                choice_keys=["pdf_tables_arabic_visual"],
                required=False,
                skip_key="pdf_tables_arabic_preserve",
            ),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        values = Inputs.parse(inputs)
        return values.mode == "labels" and "__continuation" not in inputs

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        if "__continuation" in inputs:
            try:
                prepared = Prepared.model_validate(inputs["__continuation"])
                if values.mode == "labels":
                    labels_schema(prepared.extraction).model_validate(prepared.labels.model_dump())
                elif values.mode == "source":
                    expected = source_labels(
                        prepared.extraction,
                        values.language,
                        visual_arabic=values.arabic_order == "visual",
                    )
                    if prepared.labels != expected:
                        raise ValueError("invalid source headers continuation")
                elif prepared.labels != direct_labels(prepared.extraction, values.language):
                    raise ValueError("invalid direct continuation")
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
            content = build(
                prepared.extraction,
                prepared.labels,
                language=values.language,
                enhanced=values.mode == "labels",
                visual_arabic=values.arabic_order == "visual",
                source_headers=values.mode == "source",
            )
            artifact = self.runtime.storage.save(
                "tables.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            return Result(
                preview=tr("pdf_tables_delivered", values.language),
                preview_localizations={
                    lang: tr("pdf_tables_delivered", lang) for lang in ("ar", "en")
                },
                artifacts=[artifact],
            )
        if values.mode == "labels" and self.runtime.ai is None:
            raise ServiceError("provider_config")
        if getattr(self.runtime, "tables", None) is None:
            raise ServiceError("pdf_tables_unavailable")
        try:
            data = self.runtime.storage.read(values.pdf)
            try:
                extraction = await self.runtime.tables.extract(data, "lattice")
            except DocumentError as error:
                if error.key not in {"pdf_tables_missing", "pdf_tables_quality"}:
                    raise
                extraction = await self.runtime.tables.extract(data, "stream")
        except DocumentError as error:
            raise ServiceError(error.key, transient=error.transient) from None
        labels = direct_labels(extraction, values.language)
        if values.mode == "source":
            try:
                labels = source_labels(
                    extraction, values.language, visual_arabic=values.arabic_order == "visual"
                )
            except ValueError:
                raise ServiceError("input_invalid") from None
        if values.mode == "labels":
            labels = await self.runtime.ai.extract(
                labels_schema(extraction),
                ai_source(extraction),
                LABELS.format(language={"ar": "Arabic", "en": "English"}[values.language]),
            )
        prepared = Prepared(extraction=extraction, labels=labels)
        reviews = {}
        for lang in ("ar", "en"):
            preview = [tr("pdf_tables_review", lang)]
            if values.mode == "source":
                preview.append(tr("pdf_tables_source_headers_review", lang))
            if values.arabic_order == "visual":
                preview.append(tr("pdf_tables_arabic_review", lang))
            for table_labels in sorted(labels.tables, key=lambda table: table.table_id):
                table = extraction.tables[table_labels.table_id - 1]
                preview.append(
                    tr(
                        "pdf_tables_review_table",
                        lang,
                        number=table_labels.table_id,
                        page=table.page,
                        rows=len(table.rows),
                        columns=len(table.rows[0]),
                    )
                )
                if values.mode in {"labels", "source"}:
                    preview.append(table_labels.title)
                    preview.extend(
                        f"{i}. {label}" for i, label in enumerate(table_labels.columns, 1)
                    )
                # Generic numbered columns add no information beyond the exact width.
            review = "\n".join(preview)
            if len(review) > 2800:
                raise ServiceError(
                    "input_invalid" if values.mode == "source" else "provider_invalid"
                )
            reviews[lang] = review
        return Result(
            preview=reviews[values.language],
            preview_localizations=reviews,
            needs_confirmation=True,
            continuation=prepared.model_dump(mode="json"),
        )


SERVICE = PdfTablesExcel
