"""Content-based script direction detection shared by the office builders.

Builders must not force right-to-left everywhere: Arabic content is right-aligned
and bidi-ordered while English/Latin content stays left-to-right. Mixed content
follows the dominant script so the customer's intended reading direction wins.
"""

_ARABIC_RANGES = (
    (0x0600, 0x06FF),  # Arabic
    (0x0750, 0x077F),  # Arabic Supplement
    (0x08A0, 0x08FF),  # Arabic Extended-A
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    (0x1EE00, 0x1EEFF),  # Arabic Mathematical Alphabetic Symbols
)


def _is_arabic(char: str) -> bool:
    code = ord(char)
    return any(low <= code <= high for low, high in _ARABIC_RANGES)


def _is_latin(char: str) -> bool:
    return "a" <= char <= "z" or "A" <= char <= "Z"


def has_arabic(text: str) -> bool:
    """Return True when the text contains any Arabic-script character."""
    return any(_is_arabic(char) for char in text)


def is_rtl(text: str) -> bool:
    """Return True when Arabic should govern the reading direction of text.

    English-only text is LTR, Arabic-only text is RTL, and mixed text follows the
    dominant script (Arabic wins ties because Arabic documents commonly embed
    short Latin numbers, names and acronyms).
    """
    arabic = sum(1 for char in text if _is_arabic(char))
    if arabic == 0:
        return False
    latin = sum(1 for char in text if _is_latin(char))
    return arabic >= latin
