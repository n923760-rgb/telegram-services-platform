from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.builders.word_schema import WordDocument, WordSection
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs

Text = Annotated[str, StringConstraints(strip_whitespace=False)]


class Inputs(StrictModel):
    language: Literal["ar", "en"]
    full_name: str = Field(min_length=1, max_length=120)
    contact: Text = Field(min_length=1, max_length=500)
    summary: Text | None = Field(default=None, min_length=1, max_length=1000)
    experience: Text | None = Field(default=None, min_length=1, max_length=4000)
    education: Text | None = Field(default=None, min_length=1, max_length=2000)
    skills: Text = Field(min_length=1, max_length=1500)
    additional: Text | None = Field(default=None, min_length=1, max_length=1500)

    @field_validator(
        "full_name", "contact", "summary", "experience", "education", "skills", "additional"
    )
    @classmethod
    def validate_content(cls, value):
        if value is None:
            return None
        return DocumentInputs.printable_text(value)

    @field_validator("full_name", mode="before")
    @classmethod
    def single_name(cls, value):
        return DocumentInputs.printable_title(value)

    @model_validator(mode="after")
    def bounded_cv(self):
        if not self.experience and not self.education:
            raise ValueError("provide experience or education")
        values = [
            self.full_name,
            self.contact,
            self.summary,
            self.experience,
            self.education,
            self.skills,
            self.additional,
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

    def document(self):
        sections = [WordSection(paragraphs=self.contact.split("\n"))]
        for name in ("summary", "experience", "education", "skills", "additional"):
            value = getattr(self, name)
            if value is not None:
                sections.append(
                    WordSection(
                        heading=tr("cv_" + name + "_heading", self.language),
                        paragraphs=value.split("\n"),
                    )
                )
        return WordDocument(
            title=self.full_name,
            sections=sections,
            alignment="right" if self.language == "ar" else "left",
        )
