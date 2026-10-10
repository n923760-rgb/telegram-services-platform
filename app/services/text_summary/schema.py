import json
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StringConstraints, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )
    length: Literal["short", "standard"]
    language: Literal["ar", "en"]

    @model_validator(mode="after")
    def bounded_source(self):
        self.text = DocumentInputs.printable_text(self.text)
        if not 2 <= len(self.lines()) <= 80:
            raise ValueError("summary needs 2 to 80 nonempty source paragraphs")
        return self

    def lines(self):
        return [line for line in self.text.split("\n") if line.strip()]

    def limit(self):
        return min({"short": 3, "standard": 7}[self.length], len(self.lines()) - 1)

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
            raise ServiceError("input_invalid") from None


class Selection(StrictModel):
    source_ids: list[Annotated[StrictInt, Field(ge=1, le=80)]] = Field(min_length=1, max_length=7)


def selection_schema(values):
    count, limit = len(values.lines()), values.limit()

    class SourceSelection(Selection):
        @model_validator(mode="after")
        def known_unique_bounded_ids(self):
            ids = self.source_ids
            if (
                len(ids) > limit
                or len(ids) != len(set(ids))
                or any(number > count for number in ids)
            ):
                raise ValueError("select unique known source IDs within requested point limit")
            return self

    return SourceSelection


def render(values, plan):
    lines = values.lines()
    ids = sorted(plan.source_ids)
    # Only original source strings become customer content; AI supplies IDs, never prose.
    points = "\n\n".join(f"[{number}] {lines[number - 1]}" for number in ids)
    heading = tr("text_summary_heading", values.language, selected=len(ids), total=len(lines))
    summary = heading + "\n\n" + points + "\n\n" + tr("text_summary_notice", values.language)
    source = "\n\n".join(f"[{number}] {line}" for number, line in enumerate(lines, 1))
    report = summary + "\n\n" + tr("text_summary_source_heading", values.language) + "\n\n" + source
    return summary, report
