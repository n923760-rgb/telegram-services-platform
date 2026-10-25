"""Source-bound ASCII contacts in Arabic PDF text and rendered glyph checks."""

from io import BytesIO

import pdfplumber

from app.builders.schema import Document, Section

CONTACTS = [
    "00123@e.invalid",
    "24@e.invalid",
    "2026-10-24@e.invalid",
    "2026-10-24.news@e.invalid",
    "help@e.invalid",
    "https://e.invalid/2026-10-24?i=00123&n=0",
    "www.e.invalid/2026-10-24",
]


def contact_document(contact, position="middle"):
    text = {
        "start": f"{contact} راجع الطلب",
        "middle": f"راجع {contact} لتأكيد الطلب",
        "end": f"راجع الطلب {contact}",
    }[position]
    return Document(
        title=text,
        sections=[Section(heading=text, paragraphs=[text], bullets=[text])],
    )


def check_contacts(content, contact):
    with pdfplumber.open(BytesIO(content)) as document:
        assert len(document.pages) == 1
        page = document.pages[0]
        chars = page.chars
        stream = "".join(char["text"] for char in chars)
        assert stream.count(contact) == 4
        assert not any(c in stream for c in "\u202d\u202c\u200e\u200f")
        start = 0
        for _ in range(4):
            index = stream.index(contact, start)
            glyphs = chars[index : index + len(contact)]
            assert all(a["x0"] < b["x0"] for a, b in zip(glyphs, glyphs[1:], strict=False))
            assert max(c["top"] for c in glyphs) - min(c["top"] for c in glyphs) < 0.01
            start = index + len(contact)
        assert all(40 <= c["x0"] <= c["x1"] <= page.width - 40 for c in chars)
        assert all(40 <= c["top"] <= c["bottom"] <= page.height - 18 for c in chars)
