import unicodedata

from app.services.base import ServiceError


def extract_page_text(page, *, limit: int) -> str:
    """Keep visitor fragments that pypdf's final bidi string may discard.

    Normalize only Arabic presentation forms, leaving identifiers, amounts,
    punctuation and all other source characters unchanged. This is text
    extraction, not reconstruction of the original page layout.
    """
    parts = []
    length = 0

    def collect(text, _cm, _tm, _font, _size):
        nonlocal length
        text = "".join(
            unicodedata.normalize("NFKC", char)
            if "\ufb50" <= char <= "\ufdff" or "\ufe70" <= char <= "\ufeff"
            else char
            for char in text
        )
        length += len(text)
        if length > limit:
            raise ServiceError("pdf_text_too_long")
        parts.append(text)

    page.extract_text(visitor_text=collect)
    return "".join(parts).strip()
