from pydantic import Field, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.providers.documents.base import Language
from app.services.base import ServiceError


class Inputs(StrictModel):
    images: list[str] = Field(min_length=1, max_length=5)
    language: Language

    @model_validator(mode="after")
    def distinct(self):
        if len(set(self.images)) != len(self.images):
            raise ValueError("duplicate image")
        return self

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except ValidationError:
            raise ServiceError("input_invalid") from None
