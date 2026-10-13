from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.builders.word_schema import WordDocument, WordSection
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs

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
    education: Text | None = Field(default=None, min_length=1, max_length=2000)
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

    def contact_section(self):
        return WordSection(
            paragraphs=([self.headline] if self.headline else []) + self.contact.split("\n")
        )

    def document(self):
        sections = [self.contact_section()]
        for name in self.ordered_names():
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
            layout="resume",
            sections=sections,
            alignment="right" if self.language == "ar" else "left",
        )


class EnglishContent(CvContent):
    language: Literal["en"] = "en"


class Inputs(CvContent):
    language: Literal["ar", "en", "bilingual"]
    english: EnglishContent | None = None

    @model_validator(mode="after")
    def bilingual_content(self):
        if (self.language == "bilingual") != (self.english is not None):
            raise ValueError("English content is required only for bilingual CVs")
        return self

    def document(self):
        if self.language != "bilingual":
            return super().document()
        # Both bodies are supplied final content, not inferred translations.
        arabic = CvContent.model_validate(self.model_dump(exclude={"english"}) | {"language": "ar"})
        english = self.english.model_copy(update={"cv_type": self.cv_type})
        sections = [arabic.contact_section(), english.contact_section()]
        for name in arabic.ordered_names():
            for content in (arabic, english):
                value = getattr(content, name)
                if value is not None:
                    sections.append(
                        WordSection(
                            heading=tr("cv_" + name + "_heading", content.language),
                            paragraphs=value.split("\n"),
                        )
                    )
        return WordDocument(
            title=arabic.full_name + "\n" + english.full_name,
            layout="resume",
            sections=sections,
            alignment="auto",
        )
