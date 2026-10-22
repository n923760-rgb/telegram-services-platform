"""Request-local cell evidence; conversions are literal and deliberately conservative."""

import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field, StrictInt, StringConstraints, model_validator

from app.builders.schema import StrictModel
from app.services.documents import DocumentInputs
from app.services.text_to_office.schema import ExcelPlan
from app.services.translation import NUMERIC_TOKEN

NUMBER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
CONTACT_TOKEN = re.compile(
    r"https?://[^\s<>]+|www\.[^\s<>]+|[a-z0-9.+_-]+@[a-z0-9.-]+\.[a-z0-9-]+", re.IGNORECASE
)
YEAR_DATE = re.compile(r"([0-9]{4})([-/])([0-9]{2})\2([0-9]{2})")
IDENTIFIER_HEADER = re.compile(
    r"\b(?:id|identifier|phone|telephone|mobile|account|sku|code)\b|رقم|معرف|هاتف|جوال|حساب|رمز",
    re.IGNORECASE,
)
Quote = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1, max_length=4000)]


class RowEvidence(StrictModel):
    source_id: StrictInt = Field(ge=1, le=200)
    quotes: list[Quote | None] = Field(min_length=1, max_length=20)


def source_json(values):
    return json.dumps(
        {"lines": [{"id": i, "text": line} for i, line in enumerate(values.lines(), 1)]},
        ensure_ascii=False,
    )


def value_matches(value, quote, kind, header):
    if isinstance(value, str):
        if kind == "date":
            match = YEAR_DATE.fullmatch(quote)
            if not match:
                return False
            try:
                parsed = date(int(match[1]), int(match[3]), int(match[4]))
            except ValueError:
                return False
            return parsed.year >= 1900 and value == parsed.isoformat()
        return value == quote
    if IDENTIFIER_HEADER.search(re.sub(r"[\u064b-\u065f\u0670]", "", header).replace("_", " ")):
        return False
    if isinstance(value, bool):
        return kind == "boolean" and quote.casefold() in (
            {"true", "yes", "نعم"} if value else {"false", "no", "لا"}
        )
    if type(value) not in (int, float):
        return False
    literal = quote[:-1] if kind == "percent" and quote.endswith("%") else quote
    if not NUMBER.fullmatch(literal) or (kind == "percent" and not quote.endswith("%")):
        return False
    original = Decimal(literal)
    if original == 0 and literal.startswith("-"):
        return False
    if len(original.as_tuple().digits) > 15 or -original.as_tuple().exponent > 14:
        return False
    expected = original / 100 if kind == "percent" else original
    return Decimal(str(value)) == expected


def source_excel_schema(values):
    lines = {i: line for i, line in enumerate(values.lines(), 1)}
    patterns = (NUMERIC_TOKEN, CONTACT_TOKEN)

    class SourceExcelPlan(ExcelPlan):
        evidence: list[RowEvidence] = Field(default_factory=list, max_length=200)
        context_ids: list[StrictInt] = Field(default_factory=list, max_length=200)

        @model_validator(mode="after")
        def source_fidelity(self):
            if self.missing_information:
                return self
            table = self.table
            if len(table.columns) > 20 or len(table.rows) * len(table.columns) > 1600:
                raise ValueError("Excel source output limit")
            ids = [row.source_id for row in self.evidence]
            if len(ids) != len(table.rows) or ids != sorted(set(ids)):
                raise ValueError("one ordered source line per record")
            all_ids = ids + self.context_ids
            if len(all_ids) != len(lines) or set(all_ids) != set(lines):
                raise ValueError("account for every source line exactly once")
            metadata = "\n".join([table.title, *table.columns])
            DocumentInputs.printable_text(metadata)
            for pattern in patterns:
                if not Counter(pattern.findall(metadata)) <= Counter(pattern.findall(values.text)):
                    raise ValueError("no invented numeric/contact labels")
            for row, evidence in zip(table.rows, self.evidence, strict=True):
                if len(evidence.quotes) != len(row):
                    raise ValueError("one quote per cell")
                line = lines[evidence.source_id]
                used = []
                for i, (cell, quote) in enumerate(zip(row, evidence.quotes, strict=True)):
                    if cell is None:
                        if quote is not None:
                            raise ValueError("missing cell must have no source quote")
                        continue
                    if quote is None or quote not in line:
                        raise ValueError("quote must be verbatim within this record's source line")
                    DocumentInputs.printable_text(quote)
                    kind = table.column_formats[i].kind if table.column_formats else "number"
                    if kind == "date" and re.search(r"هجري|hijri", values.text, re.IGNORECASE):
                        raise ValueError("explicit Hijri context must retain date text")
                    if not value_matches(cell, quote, kind, table.columns[i]):
                        raise ValueError(
                            "cell must retain its quoted value or an allowed typed conversion"
                        )
                    used.append(quote)
                for pattern in patterns:
                    if sum(
                        (Counter(pattern.findall(quote)) for quote in used), Counter()
                    ) != Counter(pattern.findall(line)):
                        raise ValueError("retain every numeric/contact occurrence in the record")
            if len(self.model_dump_json()) > 100000:
                raise ValueError("Excel evidence output limit")
            return self

    return SourceExcelPlan
