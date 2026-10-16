import json
import re
from collections import Counter
from typing import Annotated, ClassVar, Literal

from pydantic import (
    Field,
    StringConstraints,
    ValidationError,
    create_model,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from app.builders.direction import is_rtl
from app.builders.schema import StrictModel
from app.builders.word_schema import WordDesign, WordDocument, WordSection
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN

Text = Annotated[str, StringConstraints(strip_whitespace=False)]


class CvContent(StrictModel):
    language: Literal["ar", "en"]
    cv_type: Literal["professional", "graduate", "career_change", "academic"] = "professional"
    headline: str | None = Field(default=None, min_length=1, max_length=120)
    projects: Text | None = Field(default=None, min_length=1, max_length=2000)
    languages: Text | None = Field(default=None, min_length=1, max_length=500)
    research: Text | None = Field(default=None, min_length=1, max_length=2000)
    publications: Text | None = Field(default=None, min_length=1, max_length=2000)
    full_name: str = Field(min_length=1, max_length=120)
    contact: Text = Field(min_length=1, max_length=500)
    summary: Text | None = Field(default=None, min_length=1, max_length=1000)
    experience: Text | None = Field(default=None, min_length=1, max_length=4000)
    education: Text = Field(min_length=1, max_length=2000)
    skills: Text = Field(min_length=1, max_length=1500)
    additional: Text | None = Field(default=None, min_length=1, max_length=1500)

    @field_validator(
        "full_name",
        "headline",
        "contact",
        "summary",
        "experience",
        "education",
        "skills",
        "additional",
        "projects",
        "languages",
        "research",
        "publications",
    )
    @classmethod
    def validate_content(cls, value):
        if value is None:
            return None
        return DocumentInputs.printable_text(value)

    @field_validator("full_name", "headline", mode="before")
    @classmethod
    def single_name(cls, value):
        return None if value is None else DocumentInputs.printable_title(value)

    @model_validator(mode="after")
    def bounded_cv(self):
        values = [
            self.full_name,
            self.contact,
            self.summary,
            self.experience,
            self.education,
            self.skills,
            self.additional,
            self.headline,
            self.projects,
            self.languages,
            self.research,
            self.publications,
        ]
        if sum(len(value or "") for value in values) > 9000:
            raise ValueError("CV too large")
        if any(value is not None and len(value.split("\n")) > 100 for value in values):
            raise ValueError("too many section lines")
        return self

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(
                {key: value for key, value in inputs.items() if not key.startswith("__")}
            )
        except ValidationError:
            raise ServiceError("input_invalid") from None

    def ordered_names(self):
        orders = {
            "professional": (
                "summary",
                "experience",
                "education",
                "projects",
                "skills",
                "languages",
                "research",
                "publications",
                "additional",
            ),
            "graduate": (
                "summary",
                "education",
                "projects",
                "skills",
                "experience",
                "languages",
                "research",
                "publications",
                "additional",
            ),
            "career_change": (
                "summary",
                "skills",
                "projects",
                "experience",
                "education",
                "languages",
                "research",
                "publications",
                "additional",
            ),
            "academic": (
                "summary",
                "education",
                "research",
                "publications",
                "experience",
                "projects",
                "skills",
                "languages",
                "additional",
            ),
        }
        return orders[self.cv_type]


class Inputs(CvContent):
    language: Literal["ar", "en", "bilingual"]

    def targets(self):
        return ("ar", "en") if self.language == "bilingual" else (self.language,)

    def segments(self):
        return {
            f"{name}:{index}": {"field": name, "text": line}
            for name in ("headline", "contact", *self.ordered_names())
            if (value := getattr(self, name)) is not None
            for index, line in enumerate(value.split("\n"), 1)
            if line.strip()
        }

    def source(self):
        return json.dumps(
            {
                "full_name": self.full_name,
                "targets": self.targets(),
                "cv_type": self.cv_type,
                "segments": self.segments(),
            },
            ensure_ascii=False,
        )

    @model_validator(mode="after")
    def total_lines(self):
        if len(self.segments()) > 160:
            raise ValueError("CV source segment limit")
        return self


SectionName = Literal[
    "summary",
    "experience",
    "education",
    "projects",
    "skills",
    "languages",
    "research",
    "publications",
    "additional",
]


class RevisedSegment(StrictModel):
    id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=4000)
    presentation: Literal["paragraph", "bullet", "lead"]


class ProfileSummary(StrictModel):
    text: str = Field(min_length=1, max_length=500)
    source_ids: list[str] = Field(min_length=1, max_length=12)


class CvBody(StrictModel):
    language: Literal["ar", "en"]
    full_name: str = Field(min_length=1, max_length=120)
    segments: list[RevisedSegment] = Field(min_length=1, max_length=160)
    summary: ProfileSummary | None = None


class CvRevision(StrictModel):
    design: WordDesign
    section_order: list[SectionName] = Field(min_length=1, max_length=9)
    bodies: list[CvBody] = Field(min_length=1, max_length=2)


DOMAIN_TOKEN = re.compile(r"(?<![\w@])(?:[\w-]+\.)+[a-zA-Z]{2,}(?:/[^\s<>]*)?")
PHONE_TOKEN = re.compile(r"(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)")

# Fixed, content-free categories: never derive codes or diagnostic labels from inputs.
CV_VALIDATION_CODES = (
    "cv_section_order",
    "cv_target_languages",
    "cv_name_identifiers",
    "cv_name_script",
    "cv_source_ids",
    "cv_single_line",
    "cv_source_tokens",
    "cv_paragraph_role",
    "cv_headline_limit",
    "cv_summary_duplicate",
    "cv_summary_missing",
    "cv_summary_line",
    "cv_summary_sources",
    "cv_summary_tokens",
    "cv_output_limit",
)


def protected(text):
    identifiers = (
        CONTACT_TOKEN.findall(text) + DOMAIN_TOKEN.findall(text) + PHONE_TOKEN.findall(text)
    )
    return Counter(NUMERIC_TOKEN.findall(text)), Counter(identifiers)


def revision_schema(values):
    source = values.segments()
    names = {segment["field"] for segment in source.values()} - {"contact", "headline"}
    if values.summary is None:
        names.add("summary")

    SourceSegment = create_model(
        "CvSourceSegment",
        __base__=RevisedSegment,
        id=(Literal[tuple(source)], Field(description="Use each allowed source ID exactly once.")),
    )
    summary_refs = tuple(
        key for key, item in source.items() if item["field"] not in {"headline", "contact"}
    )
    SourceSummary = create_model(
        "CvSourceSummary",
        __base__=ProfileSummary,
        source_ids=(
            list[Literal[summary_refs]],
            Field(
                min_length=1,
                max_length=min(12, len(summary_refs)),
                json_schema_extra={"uniqueItems": True},
            ),
        ),
    )
    SourceBody = create_model(
        "CvSourceBody",
        __base__=CvBody,
        segments=(list[SourceSegment], Field(min_length=len(source), max_length=len(source))),
        language=(Literal[tuple(values.targets())], ...),
        summary=(
            SourceSummary,
            Field(
                description="Required factual profile using career references only; no numbers, dates, contacts or URLs."
            ),
        )
        if values.summary is None
        else (type(None), None),
    )

    class SourceCv(CvRevision):
        diagnostic_categories: ClassVar[dict[str, str]] = {
            code: code for code in CV_VALIDATION_CODES
        }
        section_order: list[Literal[tuple(sorted(names))]] = Field(
            min_length=len(names),
            max_length=len(names),
            description="Order every allowed section exactly once; do not add absent sections.",
            json_schema_extra={"uniqueItems": True},
        )
        bodies: list[SourceBody] = Field(
            min_length=len(values.targets()),
            max_length=len(values.targets()),
            description="Return bodies in exactly this language order: "
            + ", ".join(values.targets()),
        )

        @model_validator(mode="after")
        def fidelity(self):
            if len(self.section_order) != len(names) or set(self.section_order) != names:
                raise PydanticCustomError(
                    "cv_section_order", "order every supplied section exactly once"
                )
            if [body.language for body in self.bodies] != list(values.targets()):
                raise PydanticCustomError(
                    "cv_target_languages",
                    "return requested languages exactly once in requested order",
                )
            for body in self.bodies:
                DocumentInputs.printable_title(body.full_name)
                if protected(body.full_name) != protected(values.full_name):
                    raise PydanticCustomError("cv_name_identifiers", "preserve name identifiers")
                if (
                    is_rtl(values.full_name) == (body.language == "ar")
                    and body.full_name != values.full_name
                ):
                    raise PydanticCustomError(
                        "cv_name_script", "preserve the original-script name verbatim"
                    )
                ids = [segment.id for segment in body.segments]
                if len(ids) != len(source) or set(ids) != set(source):
                    raise PydanticCustomError(
                        "cv_source_ids", "rewrite every source ID exactly once"
                    )
                for segment in body.segments:
                    original = source[segment.id]
                    DocumentInputs.printable_text(segment.text)
                    if any(char in segment.text for char in "\n\r"):
                        raise PydanticCustomError(
                            "cv_single_line", "one complete line per source ID"
                        )
                    if protected(segment.text) != protected(original["text"]):
                        raise PydanticCustomError(
                            "cv_source_tokens",
                            "preserve per-source numeric, phone, email and URL tokens",
                        )
                    if (
                        original["field"] in {"contact", "headline", "summary"}
                        and segment.presentation != "paragraph"
                    ):
                        raise PydanticCustomError(
                            "cv_paragraph_role", "header and profile text must remain paragraphs"
                        )
                    if original["field"] == "headline" and len(segment.text) > 120:
                        raise PydanticCustomError("cv_headline_limit", "headline limit")
                if values.summary is not None and body.summary is not None:
                    raise PydanticCustomError(
                        "cv_summary_duplicate", "do not duplicate the supplied summary"
                    )
                if values.summary is None:
                    summary = body.summary
                    if summary is None:
                        raise PydanticCustomError(
                            "cv_summary_missing", "supply a short grounded professional summary"
                        )
                    DocumentInputs.printable_text(summary.text)
                    if any(char in summary.text for char in "\n\r"):
                        raise PydanticCustomError("cv_summary_line", "single summary paragraph")
                    if len(set(summary.source_ids)) != len(summary.source_ids) or any(
                        key not in source or source[key]["field"] in {"contact", "headline"}
                        for key in summary.source_ids
                    ):
                        raise PydanticCustomError(
                            "cv_summary_sources", "summary requires actual career source references"
                        )
                    if any(protected(summary.text)):
                        raise PydanticCustomError(
                            "cv_summary_tokens",
                            "summary must not introduce or duplicate numeric/contact claims",
                        )
                if (
                    sum(len(s.text) for s in body.segments)
                    + len(body.summary.text if body.summary else "")
                    > 15000
                ):
                    raise PydanticCustomError("cv_output_limit", "CV output character limit")
            return self

    return SourceCv


def document(values, revision):
    # Revalidate even injected runtimes; a forged typed/model_copy result cannot bypass fidelity.
    revision = revision_schema(values).model_validate(revision.model_dump())
    source = values.segments()
    sections = []
    for index, body in enumerate(revision.bodies):
        edited = {segment.id: segment for segment in body.segments}
        header = WordSection(
            alignment="right" if body.language == "ar" else "left",
            title=body.full_name if index else "",
            subtitle=" ".join(
                edited[key].text for key in source if source[key]["field"] == "headline"
            ),
            paragraphs=[edited[key].text for key in source if source[key]["field"] == "contact"],
            page_break_before=bool(index),
        )
        sections.append(header)
        for name in revision.section_order:
            segments = [edited[key] for key in source if source[key]["field"] == name]
            if not segments and name == "summary":
                segments = [
                    RevisedSegment(id="summary", text=body.summary.text, presentation="paragraph")
                ]
            # Preserve mixed lead/body/bullet order within each source field.
            sections.append(
                WordSection(
                    alignment="right" if body.language == "ar" else "left",
                    heading=tr("cv_" + name + "_heading", body.language),
                    blocks=[
                        {"text": segment.text, "kind": segment.presentation} for segment in segments
                    ],
                )
            )
    return WordDocument(
        title=revision.bodies[0].full_name,
        sections=sections,
        layout="resume",
        design=revision.design,
        alignment="auto",
    )
