"""Opt-in recovery of simple visual-order Arabic presentation-form cells."""

import unicodedata


def has_presentation_forms(text: str) -> bool:
    return any(0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFC for c in text)


def recover_visual_arabic(text: str) -> str:
    # Presentation forms alone do not prove storage direction. The customer must
    # explicitly select visual-order recovery; never apply this to normal Arabic.
    # Mixed digits/Latin/punctuation/marks are ambiguous and remain untouched.
    if not has_presentation_forms(text) or any(
        c not in " \n"
        and not (
            (0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFC)
            and unicodedata.category(c) == "Lo"
        )
        for c in text
    ):
        return text
    lines = [unicodedata.normalize("NFKC", line[::-1]) for line in text.split("\n")]
    result = "\n".join(lines)
    # Reject non-letter compatibility expansions (symbols, spaces inside
    # ligatures, etc.) instead of silently rewriting unfamiliar glyphs.
    if any(
        c not in " \n"
        and not (unicodedata.category(c) == "Lo" and unicodedata.name(c, "").startswith("ARABIC"))
        for c in result
    ):
        return text
    return result
