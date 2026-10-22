from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.files.upload_order import ordered_indices, single_line
from app.services.base import ServiceError


class Inputs(StrictModel):
    images: list[str] = Field(min_length=1, max_length=5)
    page_order: str | None = Field(default=None, min_length=1, max_length=32)
    orientation: Literal["auto", "portrait", "landscape"]

    @field_validator("page_order", mode="before")
    @classmethod
    def single_line_order(cls, value):
        return single_line(value)

    @model_validator(mode="after")
    def distinct(self):
        if len(set(self.images)) != len(self.images) or any(not key.strip() for key in self.images):
            raise ValueError("empty or duplicate key")
        self.source_order()
        return self

    def source_order(self):
        return ordered_indices(self.page_order, len(self.images))

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
