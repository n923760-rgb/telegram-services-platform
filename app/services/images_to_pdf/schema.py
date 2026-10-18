import re
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.services.base import ServiceError


class Inputs(StrictModel):
    images: list[str] = Field(min_length=1, max_length=5)
    page_order: str | None = Field(default=None, min_length=1, max_length=32)
    orientation: Literal["auto", "portrait", "landscape"]

    @field_validator("page_order", mode="before")
    @classmethod
    def single_line_order(cls, value):
        if isinstance(value, str) and any(char in value for char in "\r\n\u2028\u2029"):
            raise ValueError("page order must be one line")
        return value

    @model_validator(mode="after")
    def distinct(self):
        if len(set(self.images)) != len(self.images) or any(not key.strip() for key in self.images):
            raise ValueError("empty or duplicate key")
        if self.page_order is not None and not re.fullmatch(
            r"\d(?:[ \t]*[,،][ \t]*\d|[ \t]+\d)*", self.page_order
        ):
            raise ValueError("list image numbers separated by commas or spaces")
        if sorted(self.source_order()) != list(range(1, len(self.images) + 1)):
            raise ValueError("use each uploaded image exactly once")
        return self

    def source_order(self):
        if self.page_order is None:
            return list(range(1, len(self.images) + 1))
        return [int(number) for number in re.split(r"[,، \t]+", self.page_order)]

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
