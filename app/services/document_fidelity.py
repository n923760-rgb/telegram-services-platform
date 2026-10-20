"""Request-local checks for visible smart document content, before rendering."""

import re
from collections import Counter

from pydantic import model_validator
from pydantic_core import PydanticCustomError

from app.services.translation import NUMERIC_TOKEN

CONTACT_TOKEN = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
    r"|(?:https?://|www\.)[^\s<>\"'،؛]+"
)

# Fixed categories consumed only by isolated acceptance diagnostics.
DOCUMENT_DIAGNOSTICS = {
    "document_missing_body": "document_missing_body",
    "document_missing_question": "document_missing_question",
    "document_invalid_text": "document_invalid_text",
    "document_source_tokens": "document_source_tokens",
}


def visible_text(document):
    """Only customer-visible text; exclude design, flags and clarification metadata."""
    parts = [document.title]
    for section in document.sections:
        parts.extend([section.heading, *section.paragraphs, *section.bullets])
        parts.extend([getattr(section, "title", ""), getattr(section, "subtitle", "")])
        parts.extend(block.text for block in getattr(section, "blocks", []))
        for table in getattr(section, "tables", []):
            parts.extend([table.caption, *table.columns])
            parts.extend(cell for row in table.rows for cell in row)
    return "\n".join(parts)


def source_document_schema(plan_type, source):
    # Captured privately per request; no source content in schemas or validation errors.
    expected_numbers = Counter(NUMERIC_TOKEN.findall(source))
    expected_contacts = Counter(CONTACT_TOKEN.findall(source))

    class SourceDocumentPlan(plan_type):
        @model_validator(mode="after")
        def source_fidelity(self):
            if self.missing_information:
                return self
            text = visible_text(self.document)
            if any(
                (ord(c) < 32 and c not in "\t\r\n")
                or 0xD800 <= ord(c) <= 0xDFFF
                or ord(c) in {0xFFFE, 0xFFFF}
                for c in text
            ):
                raise PydanticCustomError("document_invalid_text", "invalid document text")
            if (
                Counter(NUMERIC_TOKEN.findall(text)) != expected_numbers
                or Counter(CONTACT_TOKEN.findall(text)) != expected_contacts
            ):
                raise PydanticCustomError(
                    "document_source_tokens",
                    "preserve source numeric and contact tokens and counts verbatim",
                )
            return self

    return SourceDocumentPlan
