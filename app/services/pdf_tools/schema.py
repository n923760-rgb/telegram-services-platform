from typing import Literal

from pydantic import Field, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.files.pdf_selection import page_selection
from app.services.base import ServiceError


class Inputs(StrictModel):
    operation: Literal["merge", "extract"]
    files: list[str] = Field(min_length=1, max_length=5)
    pages: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def valid_operation(self):
        if len(set(self.files)) != len(self.files):
            raise ValueError("duplicate PDF input")
        if self.operation == "merge":
            if len(self.files) < 2 or self.pages is not None:
                raise ValueError("merge requires two to five PDFs")
        elif len(self.files) != 1 or self.pages is None:
            raise ValueError("extraction requires one PDF and pages")
        else:
            page_selection(self.pages)
        return self

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
