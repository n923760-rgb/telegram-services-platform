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
)


class PdfTablesExcel(BaseService):
    slug = "pdf_tables_excel"
    name_ar = tr("pdf_tables_name")
    name_en = tr("pdf_tables_name", "en")
    description_ar = tr("pdf_tables_description")
    price_sar = Decimal("5.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="pdf", kind="file", prompt_key="pdf_tables_file"),
            InputField(
                name="method",
                prompt_key="pdf_tables_method",
                choices=["lattice", "stream"],
                choice_keys=["pdf_tables_lattice", "pdf_tables_stream"],
            ),
            InputField(
                name="mode",
                prompt_key="pdf_tables_mode",
                choices=["direct", "labels"],
                choice_keys=["pdf_tables_direct", "pdf_tables_labels"],
            ),
            InputField(
                name="language",
                prompt_key="pdf_tables_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
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
                elif prepared.labels != direct_labels(prepared.extraction, values.language):
                    raise ValueError("invalid direct continuation")
            except (ValidationError, ValueError):
                raise ServiceError("provider_invalid") from None
            content = build(
                prepared.extraction,
                prepared.labels,
                language=values.language,
                enhanced=values.mode == "labels",
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
            extraction = await self.runtime.tables.extract(
                self.runtime.storage.read(values.pdf), values.method
            )
        except DocumentError as error:
            raise ServiceError(error.key, transient=error.transient) from None
        labels = direct_labels(extraction, values.language)
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
                if values.mode == "labels":
                    preview.append(table_labels.title)
                    preview.extend(
                        f"{i}. {label}" for i, label in enumerate(table_labels.columns, 1)
                    )
                # Generic numbered columns add no information beyond the exact width.
            review = "\n".join(preview)
            if len(review) > 2800:
                raise ServiceError("provider_invalid")
            reviews[lang] = review
        return Result(
            preview=reviews[values.language],
            preview_localizations=reviews,
            needs_confirmation=True,
            continuation=prepared.model_dump(mode="json"),
        )


SERVICE = PdfTablesExcel
