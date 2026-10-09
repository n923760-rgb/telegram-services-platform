from typing import Annotated, Literal

from pydantic import (
    Field,
    StrictInt,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from app.builders.schema import StrictModel
from app.builders.word_schema import WordDocument, WordSection
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    language: Literal["ar", "en"]
    notes: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )

    @field_validator("title", mode="before")
    @classmethod
    def valid_title(cls, value):
        return DocumentInputs.printable_title(value)

    @model_validator(mode="after")
    def valid_notes(self):
        self.notes = DocumentInputs.printable_text(self.notes)
        lines = self.lines()
        if not 1 <= len(lines) <= 80 or any(len(line) > 1200 for line in lines):
            raise ValueError("meeting note limits")
        return self

    def lines(self):
        return [line for line in self.notes.split("\n") if line.strip()]

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("input_invalid") from None


class Assignment(StrictModel):
    note_id: StrictInt = Field(ge=1, le=80)
    category: Literal["discussion", "decision", "action", "review"]


class Classification(StrictModel):
    assignments: list[Assignment] = Field(min_length=1, max_length=80)


def classification_schema(notes):
    expected = set(range(1, len(notes) + 1))

    class SourceClassification(Classification):
        @model_validator(mode="after")
        def all_source_notes_once(self):
            ids = [item.note_id for item in self.assignments]
            if len(ids) != len(expected) or set(ids) != expected:
                raise ValueError("assign every source note exactly once without extra IDs")
            return self

    return SourceClassification


def document(values, plan):
    notes = values.lines()
    sections = []
    for category in ("discussion", "decision", "action", "review"):
        ids = sorted(item.note_id for item in plan.assignments if item.category == category)
        if ids:
            sections.append(
                WordSection(
                    heading=tr("minutes_" + category, values.language),
                    paragraphs=[f"[{number}] {notes[number - 1]}" for number in ids],
                )
            )
    return WordDocument(
        title=values.title,
        sections=sections,
        alignment="right" if values.language == "ar" else "left",
    )
