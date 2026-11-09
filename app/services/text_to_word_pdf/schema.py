import json
from collections import Counter
from typing import Literal

from pydantic import Field, StrictInt, field_validator, model_validator

from app.builders.schema import StrictModel
from app.builders.word_schema import WordDesign, WordDocument
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(DocumentInputs):
    formatting_notes: str | None = Field(default=None, min_length=1, max_length=1000)

    @field_validator("formatting_notes")
    @classmethod
    def safe_notes(cls, value):
        return cls.printable_text(value) if value is not None else value

    mode: Literal["direct", "smart"] = "smart"
    output_format: Literal["word", "pdf", "both"] = "both"

    @model_validator(mode="after")
    def explicit_title(self):
        if self.mode == "direct" and self.formatting_notes is not None:
            raise ValueError("formatting notes require smart mode")
        if self.mode == "direct" and self.text.count("\n") >= 10000:
            raise ValueError("too many document lines")
        if self.mode == "smart" and (
            len(self.text) > 9000
            or len(self.lines()) > 80
            or any(len(line) > 4000 for line in self.lines())
        ):
            raise ValueError("smart document source limit")
        return self

    def lines(self):
        return [line for line in self.text.split("\n") if line.strip()]

    def source(self):
        return json.dumps(
            {
                "title": self.title,
                "formatting_notes": self.formatting_notes,
                "segments": [{"id": i, "text": line} for i, line in enumerate(self.lines(), 1)],
            },
            ensure_ascii=False,
        )


class Segment(StrictModel):
    id: StrictInt = Field(ge=1, le=80)
    text: str = Field(min_length=1, max_length=4000)
    kind: Literal["paragraph", "bullet", "lead"] = "paragraph"


class Section(StrictModel):
    heading: str = Field(default="", max_length=200)
    segments: list[Segment] = Field(min_length=1, max_length=80)


class Revision(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    design: WordDesign
    sections: list[Section] = Field(min_length=1, max_length=30)


def revision_schema(values):
    patterns = (NUMERIC_TOKEN, CONTACT_TOKEN)
    expected = {
        i: [Counter(pattern.findall(line)) for pattern in patterns]
        for i, line in enumerate(values.lines(), 1)
    }

    class SourceRevision(Revision):
        @model_validator(mode="after")
        def source_fidelity(self):
            segments = [item for section in self.sections for item in section.segments]
            if [item.id for item in segments] != list(expected):
                raise ValueError("retain every source ID once in its original order")
            if values.title is not None and self.title != values.title:
                raise ValueError("preserve the supplied title verbatim")
            labels = [section.heading for section in self.sections]
            if values.title is None:
                labels.append(self.title)
            for label in labels:
                if label:
                    DocumentInputs.printable_title(label)
                    if any(pattern.findall(label) for pattern in patterns):
                        raise ValueError("headings must not add or repeat numeric/contact claims")
            for item in segments:
                DocumentInputs.printable_text(item.text)
                if any(c in item.text for c in "\r\n\u2028\u2029"):
                    raise ValueError("one block per source ID")
                actual = [Counter(pattern.findall(item.text)) for pattern in patterns]
                if actual != expected[item.id]:
                    raise ValueError(
                        "retain numeric/contact tokens within their original source ID"
                    )
            notes = values.formatting_notes
            if notes and notes not in values.text:
                visible = [
                    self.title,
                    *[s.heading for s in self.sections],
                    *[s.text for s in segments],
                ]
                if any(notes in text for text in visible):
                    raise ValueError("formatting notes must not become document content")
            if sum(len(item.text) for item in segments) > 18000:
                raise ValueError("smart document output limit")
            return self

    return SourceRevision


def refined_document(revision):
    # Source IDs stay complete in validation/review. A literal first-line title
    # is represented once by the document title, never dropped from the output.
    sections = []
    first = True
    total = sum(len(section.segments) for section in revision.sections)
    for section in revision.sections:
        blocks = []
        heading = section.heading
        for item in section.segments:
            if first and total > 1 and item.text == revision.title:
                first = False
                continue
            first = False
            blocks.append({"text": item.text, "kind": item.kind})
        if blocks:
            if (
                heading.strip().rstrip(":：").strip()
                == blocks[0]["text"].strip().rstrip(":：").strip()
            ):
                heading = ""
            sections.append({"heading": heading, "blocks": blocks})
    return WordDocument(title=revision.title, design=revision.design, sections=sections)
