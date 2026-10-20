from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.files.pdf_selection import page_selection
from app.files.upload_order import ordered_indices, single_line
from app.services.base import ServiceError


class Inputs(StrictModel):
    operation: Literal["merge", "extract", "rotate"]
    files: list[str] = Field(min_length=1, max_length=5)
    file_order: str | None = Field(default=None, min_length=1, max_length=32)
    pages: str | None = Field(default=None, min_length=1, max_length=200)
    rotation: Literal["90", "180", "270"] | None = None

    @field_validator("file_order", mode="before")
    @classmethod
    def one_line_order(cls, value):
        return single_line(value)

    @model_validator(mode="after")
    def valid_operation(self):
        if self.operation != "merge" and self.file_order is not None:
            raise ValueError("file order belongs to merge only")
        if (self.operation == "rotate") != (self.rotation is not None):
            raise ValueError("rotation angle belongs to page rotation only")
        if len(set(self.files)) != len(self.files):
            raise ValueError("duplicate PDF input")
        if self.operation == "merge":
            if len(self.files) < 2 or self.pages is not None:
                raise ValueError("merge requires two to five PDFs")
            self.source_order()
        elif len(self.files) != 1 or self.pages is None:
            raise ValueError("extraction or rotation requires one PDF and pages")
        else:
            page_selection(self.pages)
        return self

    def source_order(self):
        return ordered_indices(self.file_order, len(self.files))

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
