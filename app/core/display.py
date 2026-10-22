"""Display-only references and bounded plain-text message parts."""

from uuid import UUID


def order_reference(value):
    """Keep complete UUIDs in callbacks/database and order details."""
    try:
        return UUID(str(value)).hex[:8].upper()
    except (ValueError, TypeError, AttributeError):
        return str(value)


def message_parts(text, limit=3500):
    part, units = [], 0
    for character in text:
        size = 2 if ord(character) > 0xFFFF else 1
        if units + size > limit:
            yield "".join(part)
            part, units = [], 0
        part.append(character)
        units += size
    if part:
        yield "".join(part)


def result_preview(result, language):
    if result.get("needs_confirmation"):
        details = result.get("review_details_localizations", {}).get(language) or result.get(
            "review_details", ""
        )
        if details:
            return details
    return result.get("preview_localizations", {}).get(language, result.get("preview", ""))
