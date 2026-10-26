from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    language: Literal["ar", "en"]
    entries: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=10000
    )

    @model_validator(mode="after")
    def valid_entries(self):
        self.rows()
        return self

    def rows(self):
        rows = self.entries.split("\n")
        if not 1 <= len(rows) <= 24:
            raise ValueError("one to 24 rows required")
        result = []
        for row in rows:
            label, separator, payload = row.partition("|")
            label = label.strip()
            DocumentInputs.printable_text(label)
            DocumentInputs.printable_text(payload)
            if (
                not separator
                or not 1 <= len(label) <= 40
                or not 1 <= len(payload.encode("utf-8")) <= 240
            ):
                raise ValueError("invalid QR entry")
            if any(not c.isprintable() for c in label + payload):
                raise ValueError("printable single-line content required")
            result.append((label, payload))
        return result

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except (ValidationError, ValueError):
            raise ServiceError("input_invalid") from None
