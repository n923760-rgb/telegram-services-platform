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


def include_conversion_title(document: WordDocument, source: str) -> bool:
    """Hide a header-derived cover title only for an otherwise untitled table.

    Keep all reviewed cells and preserve ambiguous sources, protected literals,
    explicit breaks, captions and any surrounding prose. Never mutate the plan.
    """
    title = " ".join(document.title.split())
    if document.layout != "standard" or NUMERIC_TOKEN.search(title) or CONTACT_TOKEN.search(title):
        return True
    tables = []
    for section in document.sections:
        if (
            section.title
            or section.subtitle
            or section.heading
            or section.paragraphs
            or section.bullets
            or section.blocks
            or section.page_break_before
        ):
            return True
        tables.extend(section.tables)
    if len(tables) != 1 or tables[0].caption:
        return True
    headers = " ".join(" ".join(column.split()) for column in tables[0].columns)
    if title != headers:
        return True
    table_text = " ".join([*tables[0].columns, *(cell for row in tables[0].rows for cell in row)])
    return " ".join(source.split()) != " ".join(table_text.split())
