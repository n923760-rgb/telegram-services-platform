from collections import Counter
from typing import ClassVar

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from app.builders.schema import Document, StrictModel
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    pdf: str = Field(min_length=1, max_length=12000)


class WordPlan(StrictModel):
    diagnostic_categories: ClassVar = {
        "pdf_word_missing_body": "pdf_word_missing_body",
        "pdf_word_source_tokens": "pdf_word_source_tokens",
    }
    missing_information: bool = Field(
        default=False,
        description="Keep false: the supplied extracted text is the complete conversion input, including sparse tables or fragments. No additional customer facts are required.",
    )
    document: Document | None = Field(
        default=None,
        description="Required editable document containing all supplied extracted content. Preserve incomplete notes as incomplete notes; do not request missing context or invent facts.",
    )


def source_plan_schema(source: str):
    """Require conversion of supplied text; preserve existing literal fidelity."""
    patterns = (NUMERIC_TOKEN, CONTACT_TOKEN)
    expected = tuple(Counter(pattern.findall(source)) for pattern in patterns)

    class SourceWordPlan(WordPlan):
        document: Document = Field(
            description="Required complete editable conversion of the supplied extracted text, including sparse notes or cell values without adding context.",
        )

        @model_validator(mode="before")
        @classmethod
        def require_conversion_body(cls, value):
            if isinstance(value, dict) and (
                value.get("document") is None or value.get("missing_information") is True
            ):
                raise PydanticCustomError(
                    "pdf_word_missing_body",
                    "convert the supplied extracted text without requesting additional facts",
                )
            return value

        @model_validator(mode="after")
        def supplied_text_requires_document(self):
            if self.missing_information or self.document is None:
                raise PydanticCustomError(
                    "pdf_word_missing_body",
                    "convert the supplied extracted text without requesting additional facts",
                )
            parts = [self.document.title]
            for section in self.document.sections:
                parts.extend([section.heading, *section.paragraphs, *section.bullets])
            for part in parts:
                if part:
                    DocumentInputs.printable_text(part)
            for pattern, tokens in zip(patterns, expected, strict=True):
                actual = Counter(token for part in parts for token in pattern.findall(part))
                if actual != tokens:
                    raise PydanticCustomError(
                        "pdf_word_source_tokens",
                        "preserve all extracted numeric/contact tokens and counts verbatim",
                    )
            return self

    return SourceWordPlan
