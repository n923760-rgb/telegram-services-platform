from collections import Counter

from pydantic import Field, model_validator

from app.builders.schema import Document, StrictModel
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    pdf: str = Field(min_length=1, max_length=12000)


class WordPlan(StrictModel):
    missing_information: bool = False
    document: Document | None = None


def source_plan_schema(source: str):
    """Protect extracted facts, not PDF reading order or semantic association."""
    patterns = (NUMERIC_TOKEN, CONTACT_TOKEN)
    expected = tuple(Counter(pattern.findall(source)) for pattern in patterns)

    class SourceWordPlan(WordPlan):
        @model_validator(mode="after")
        def preserve_source_tokens(self):
            if self.missing_information or self.document is None:
                return self  # The service rejects these before saving an artifact.
            parts = [self.document.title]
            for section in self.document.sections:
                parts.extend([section.heading, *section.paragraphs, *section.bullets])
            for part in parts:
                if part:
                    DocumentInputs.printable_text(part)
            for pattern, tokens in zip(patterns, expected, strict=True):
                actual = Counter(token for part in parts for token in pattern.findall(part))
                if actual != tokens:
                    raise ValueError(
                        "preserve all extracted numeric/contact tokens and counts verbatim"
                    )
            return self

    return SourceWordPlan
