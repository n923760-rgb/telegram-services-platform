import json
from collections import Counter
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StringConstraints, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )
    length: Literal["short", "standard"]
    language: Literal["ar", "en"]

    @model_validator(mode="after")
    def bounded_source(self):
        self.text = DocumentInputs.printable_text(self.text)
        if not 1 <= len(self.lines()) <= 80:
            raise ValueError("summary needs 1 to 80 nonempty source paragraphs")
        return self

    def lines(self):
        return [line for line in self.text.split("\n") if line.strip()]

    def limit(self):
        return {"short": 3, "standard": 7}[self.length]

    def source(self):
        return json.dumps(
            {"paragraphs": [{"id": i, "text": line} for i, line in enumerate(self.lines(), 1)]},
            ensure_ascii=False,
        )

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("text_summary_invalid") from None


class Point(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=1200
    )
    source_ids: list[Annotated[StrictInt, Field(ge=1, le=80)]] = Field(min_length=1, max_length=80)


class Summary(StrictModel):
    points: list[Point] = Field(min_length=1, max_length=7)


def summary_schema(values):
    count, limit = len(values.lines()), values.limit()

    class SourceSummary(Summary):
        @model_validator(mode="after")
        def grounded_points(self):
            if len(self.points) > limit:
                raise ValueError("summary point limit")
            seen = set()
            for point in self.points:
                ids = point.source_ids
                if len(ids) != len(set(ids)) or any(number > count for number in ids):
                    raise ValueError("cite unique known source IDs")
                DocumentInputs.printable_text(point.text)
                if "\n" in point.text or "\r" in point.text or point.text.strip() != point.text:
                    raise ValueError("one clean paragraph per point")
                if point.text in seen:
                    raise ValueError("duplicate summary point")
                seen.add(point.text)
                cited = "\n".join(values.lines()[number - 1] for number in ids)
                for pattern in (NUMERIC_TOKEN, CONTACT_TOKEN):
                    if Counter(pattern.findall(point.text)) - Counter(pattern.findall(cited)):
                        raise ValueError("summary numbers and contacts must occur in cited source")
            if sum(len(point.text) for point in self.points) > 6000:
                raise ValueError("summary output limit")
            if len(values.text.split()) >= 40 and sum(
                len(point.text.split()) for point in self.points
            ) >= len(values.text.split()):
                raise ValueError("summary must shorten the source")
            return self

    return SourceSummary


def render(values, plan):
    references = [
        ", ".join(f"[{number}]" for number in sorted(point.source_ids)) for point in plan.points
    ]
    points = "\n\n".join(
        f"• [{index}] {point.text}\n"
        + tr("text_summary_point_sources", values.language, references=references[index - 1])
        for index, point in enumerate(plan.points, 1)
    )
    heading = tr("text_summary_heading", values.language)
    summary = heading + "\n\n" + points + "\n\n" + tr("text_summary_notice", values.language)
    citations = "\n".join(f"[{i}] {references[i - 1]}" for i in range(1, len(plan.points) + 1))
    source = "\n\n".join(f"[{i}] {line}" for i, line in enumerate(values.lines(), 1))
    report = (
        summary
        + "\n\n"
        + tr("text_summary_references", values.language)
        + "\n"
        + citations
        + "\n\n"
        + tr("text_summary_source_heading", values.language)
        + "\n\n"
        + source
        + "\n\n"
        + tr("text_summary_original", values.language)
        + "\n\n"
        + values.text
    )
    return summary, report
