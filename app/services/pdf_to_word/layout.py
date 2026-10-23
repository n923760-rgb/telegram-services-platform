"""Conservative presentation cleanup after source fidelity and AI review."""

from pydantic import ValidationError

from app.builders.word_schema import WordDocument
from app.services.document_fidelity import visible_text
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


def opening_title(document: WordDocument, source: str) -> WordDocument:
    """Keep the document title when AI repeats it as the first section heading.

    Only an exact, single source line and exactly two candidate occurrences
    qualify. Protected tokens, explicit page breaks and later headings retain
    their original presentation. The reviewed plan is never mutated.
    """
    title = " ".join(document.title.split())
    if document.layout != "standard" or NUMERIC_TOKEN.search(title) or CONTACT_TOKEN.search(title):
        return document
    if sum(" ".join(line.split()) == title for line in source.splitlines()) != 1:
        return document
    if sum(" ".join(line.split()) == title for line in visible_text(document).splitlines()) != 2:
        return document
    for index, section in enumerate(document.sections):
        if section.page_break_before:
            return document
        if section.title:
            field = "title"
        elif section.subtitle:
            return document
        elif section.heading:
            field = "heading"
        elif section.paragraphs or section.bullets or section.blocks or section.tables:
            return document
        else:
            continue
        if " ".join(getattr(section, field).split()) != title:
            return document
        candidate = document.model_dump()
        candidate["sections"][index][field] = ""
        try:
            return WordDocument.model_validate(candidate)
        except ValidationError:
            # A heading-only document still needs its nonempty body contract.
            return document
    return document
