import re
from collections import Counter
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
from app.builders.word_schema import WordDocument, WordSection, WordTable
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.translation import NUMERIC_TOKEN

_SENTENCE_GAP = re.compile(r"(?<=[.!?؟؛;])\s+(?=\S)")
_NAME_TITLES = {"dr.", "mr.", "mrs.", "ms.", "prof.", "د.", "م.", "أ.", "ا."}


def note_units(line):
    """Conservatively retain familiar dotted names; explicit newlines stay authoritative."""
    start = 0
    for gap in _SENTENCE_GAP.finditer(line):
        if line[gap.start() - 1] == ".":
            token = re.search(r"\S+$", line[: gap.start()]).group().lstrip("([{\"'«“‘")
            if (
                token.lower() in _NAME_TITLES
                or re.fullmatch(r"[A-Z]\.", token)
                or re.fullmatch(r"(?:[A-Za-z]\.){2,}", token)
                or re.fullmatch(r"\d{1,3}\.", line[start : gap.start()].strip())
            ):
                continue
        yield line[start : gap.start()]
        start = gap.end()
    yield line[start:]


class Inputs(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
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
        # Quote original slices; do not infer relationships across ambiguous units.
        return [
            part for line in self.notes.split("\n") for part in note_units(line) if part.strip()
        ]

    def document_title(self):
        return self.title if self.title is not None else tr("minutes_default_title", self.language)

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("minutes_input_invalid") from None


class Assignment(StrictModel):
    note_id: StrictInt = Field(ge=1, le=80)
    category: Literal["discussion", "decision", "action", "review"]
    assignee: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        default="",
        max_length=200,
        description="Complete verbatim assignee name/role from this note, or empty if unspecified. Never infer.",
    )
    deadline: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        default="",
        max_length=200,
        description="Verbatim explicit task deadline from this note, or empty if unspecified. Preserve date notation and conditions.",
    )


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
            for item in self.assignments:
                if item.category != "action" and (item.assignee or item.deadline):
                    raise ValueError("only explicit actions may carry task metadata")
                source = notes[item.note_id - 1]
                for value in (item.assignee, item.deadline):
                    if value and (
                        value not in source
                        or "\n" in value
                        or "\r" in value
                        or Counter(NUMERIC_TOKEN.findall(value))
                        - Counter(NUMERIC_TOKEN.findall(source))
                    ):
                        raise ValueError(
                            "task metadata must quote this source note and whole numeric tokens"
                        )
            return self

    return SourceClassification


def document(values, plan):
    notes = values.lines()
    sections = []
    for category in ("discussion", "decision", "action", "review"):
        ids = sorted(item.note_id for item in plan.assignments if item.category == category)
        if ids:
            tasks = {item.note_id: item for item in plan.assignments}
            tables = []
            if category == "action":
                tables = [
                    WordTable(
                        caption=tr("minutes_action_register", values.language),
                        columns=[
                            tr("minutes_task_reference", values.language),
                            tr("minutes_assignee", values.language),
                            tr("minutes_deadline", values.language),
                        ],
                        rows=[
                            [
                                f"[{number}]",
                                tasks[number].assignee
                                or tr("minutes_unspecified", values.language),
                                tasks[number].deadline
                                or tr("minutes_unspecified", values.language),
                            ]
                            for number in ids
                        ],
                    )
                ]
            sections.append(
                WordSection(
                    heading=tr("minutes_" + category, values.language),
                    paragraphs=[f"[{number}] {notes[number - 1]}" for number in ids],
                    tables=tables,
                )
            )
    return WordDocument(
        title=values.document_title(),
        sections=sections,
        alignment="right" if values.language == "ar" else "left",
    )
