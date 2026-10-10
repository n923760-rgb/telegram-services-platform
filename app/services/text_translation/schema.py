import json
from collections import Counter
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StringConstraints, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )
    language: Literal["ar", "en"]
    style: Literal["formal", "business", "academic", "casual"] = "formal"

    @model_validator(mode="after")
    def bounded_text(self):
        self.text = DocumentInputs.printable_text(self.text)
        if len(self.lines()) > 80:
            raise ValueError("translation line limit")
        return self

    def lines(self):
        return [line for line in self.text.split("\n") if line.strip()]

    def source(self):
        return json.dumps(
            {"segments": [{"id": i, "text": line} for i, line in enumerate(self.lines(), 1)]},
            ensure_ascii=False,
        )

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("input_invalid") from None


class Segment(StrictModel):
    id: StrictInt = Field(ge=1, le=80)
    text: str = Field(
        min_length=1,
        max_length=24000,
        description="Full translated source line, no commentary or newlines; numeric tokens verbatim.",
    )


class Translation(StrictModel):
    segments: list[Segment] = Field(min_length=1, max_length=80)


def translation_schema(values):
    expected = {i: Counter(NUMERIC_TOKEN.findall(line)) for i, line in enumerate(values.lines(), 1)}

    class SourceTranslation(Translation):
        @model_validator(mode="after")
        def source_fidelity(self):
            ids = [segment.id for segment in self.segments]
            if len(ids) != len(expected) or set(ids) != set(expected):
                raise ValueError("translate every source ID exactly once")
            for segment in self.segments:
                DocumentInputs.printable_text(segment.text)
                if "\n" in segment.text or "\r" in segment.text:
                    raise ValueError("one translated line per source ID")
                if Counter(NUMERIC_TOKEN.findall(segment.text)) != expected[segment.id]:
                    raise ValueError("preserve source numeric tokens per line verbatim")
            if len(render(values, self)) > 24000:
                raise ValueError("translation output limit")
            return self

    return SourceTranslation


def render(values, translation):
    translated = {segment.id: segment.text for segment in translation.segments}
    number = 0
    output = []
    for line in values.text.split("\n"):
        if line.strip():
            number += 1
            output.append(translated[number])
        else:
            output.append(line)
    return "\n".join(output)
