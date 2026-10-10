from typing import Literal

from pydantic import Field, ValidationError

from app.builders.schema import StrictModel
from app.services.base import ServiceError


class Inputs(StrictModel):
    image: str = Field(min_length=1, max_length=200)
    mode: Literal["contrast", "grayscale"]

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
