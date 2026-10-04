from typing import Literal

from pydantic import Field

from app.builders.schema import StrictModel


class Inputs(StrictModel):
    images: list[str] = Field(min_length=1, max_length=5)
    language: Literal["none", "ar", "en"] = "none"
    style: Literal["formal", "business", "academic", "casual"] = "formal"


class Extracted(StrictModel):
    readable: bool
    confidence: float = Field(ge=0, le=1)
    text: str = Field(max_length=50000)


class Translation(StrictModel):
    text: str = Field(min_length=1, max_length=50000)
