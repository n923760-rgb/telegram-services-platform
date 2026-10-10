import json
from typing import Literal

from pydantic import Field, StrictInt, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.core.i18n import tr
from app.providers.tables.base import Extraction
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    pdf: str = Field(min_length=1, max_length=250)
    method: Literal["lattice", "stream"]
    mode: Literal["direct", "labels"]
    language: Literal["ar", "en"]

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("input_invalid") from None


class TableLabels(StrictModel):
    table_id: StrictInt = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=100)
    columns: list[str] = Field(min_length=2, max_length=12)

    @model_validator(mode="after")
    def valid_labels(self):
        for text in [self.title, *self.columns]:
            DocumentInputs.printable_text(text)
            if len(text) > 100 or any(c in text for c in "\r\n\u2028\u2029"):
                raise ValueError("single-line descriptive labels only, without numbers")
        if len({name.casefold() for name in self.columns}) != len(self.columns):
            raise ValueError("unique column labels")
        return self


class Labels(StrictModel):
    tables: list[TableLabels] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def review_budget(self):
        if sum(len(text) for table in self.tables for text in [table.title, *table.columns]) > 1800:
            raise ValueError("headings must fit the complete customer review")
        return self


def labels_schema(extraction):
    widths = {i: len(table.rows[0]) for i, table in enumerate(extraction.tables, 1)}

    class SourceLabels(Labels):
        @model_validator(mode="after")
        def exact_shapes(self):
            ids = [table.table_id for table in self.tables]
            if len(ids) != len(widths) or set(ids) != set(widths):
                raise ValueError("label every source table exactly once")
            if any(
                NUMERIC_TOKEN.search(text)
                for table in self.tables
                for text in [table.title, *table.columns]
            ):
                raise ValueError("AI labels must not contain numeric claims")
            if any(len(table.columns) != widths[table.table_id] for table in self.tables):
                raise ValueError("label every source column exactly once")
            return self

    return SourceLabels


def direct_labels(extraction, language):
    return Labels(
        tables=[
            TableLabels(
                table_id=i,
                title=tr("pdf_tables_table", language, number=i),
                columns=[
                    tr("pdf_tables_column", language, number=c)
                    for c in range(1, len(table.rows[0]) + 1)
                ],
            )
            for i, table in enumerate(extraction.tables, 1)
        ]
    )


class Prepared(StrictModel):
    extraction: Extraction
    labels: Labels


def ai_source(extraction):
    return json.dumps(
        {
            "tables": [
                {
                    "table_id": i,
                    "columns": len(table.rows[0]),
                    "sample_rows": [[cell[:80] for cell in row] for row in table.rows[:2]],
                }
                for i, table in enumerate(extraction.tables, 1)
            ]
        },
        ensure_ascii=False,
    )
