import csv
from io import StringIO
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )
    delimiter: Literal["comma", "semicolon", "tab"]
    whitespace: Literal["preserve", "trim"]
    language: Literal["ar", "en"]

    @model_validator(mode="after")
    def valid_csv(self):
        self.text = DocumentInputs.printable_text(self.text)
        self.records()
        return self

    def records(self):
        delimiter = {"comma": ",", "semicolon": ";", "tab": "\t"}[self.delimiter]
        try:
            records = list(
                csv.reader(
                    StringIO(self.text.removeprefix("\ufeff")), delimiter=delimiter, strict=True
                )
            )
        except csv.Error:
            raise ValueError("invalid CSV") from None
        if not 2 <= len(records) <= 501:
            raise ValueError("require a header and 1 to 500 records")
        headers = records[0]
        normalized = [value.strip() for value in headers]
        if not 1 <= len(headers) <= 20 or any(
            not value or len(original) > 80 or any(c in value for c in "\n\u2028\u2029")
            for original, value in zip(headers, normalized, strict=True)
        ):
            raise ValueError("invalid header")
        if len({value.casefold() for value in normalized}) != len(headers):
            raise ValueError("duplicate headers")
        rows = [row or [""] * len(headers) for row in records[1:]]
        if any(len(row) != len(headers) or any(len(value) > 500 for value in row) for row in rows):
            raise ValueError("ragged or oversized CSV")
        # Bound multiline wrapping so every supported cell remains readable.
        if any(value.count("\n") > 10 for row in rows for value in row):
            raise ValueError("too many cell lines")
        return headers, rows

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
