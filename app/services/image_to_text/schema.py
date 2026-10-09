import re
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

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
    text: str = Field(
        min_length=1,
        max_length=50000,
        description=(
            "Translate all source prose without additions or omissions. Preserve each numeric "
            "token verbatim, including signs, separators, leading zeros, date notation, "
            "percent signs and repetitions. Do not convert dates, units or currencies."
        ),
    )


NUMERIC_TOKEN = re.compile(r"[+\-−]?\d+(?:[.,:/\-٫٬]\d+)*(?:[%٪])?")


def translation_schema(source: str):
    # Request-local validation lets the existing gateway apply its one repair.
    # Source values are not embedded in JSON Schema or a shared mutable model.
    expected = Counter(NUMERIC_TOKEN.findall(source))

    class NumericTranslation(Translation):
        @model_validator(mode="after")
        def preserve_numeric_tokens(self):
            if Counter(NUMERIC_TOKEN.findall(self.text)) != expected:
                raise ValueError("preserve source numeric tokens and occurrence counts verbatim")
            return self

    return NumericTranslation
