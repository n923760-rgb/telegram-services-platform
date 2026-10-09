import csv
import math
from io import StringIO

from app.providers.documents.base import DocumentError, Recognition

MAX_OUTPUT = 2 * 1024 * 1024
MAX_TEXT = 50000


def parse(data: bytes) -> Recognition:
    """Keep recognized words/line order. Confidence is a rejection gate, not proof."""
    if not data or len(data) > MAX_OUTPUT:
        raise DocumentError("local_ocr_limit")
    try:
        # Tesseract TSV text is unquoted: quotation marks are recognized content.
        rows = csv.DictReader(
            StringIO(data.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE, strict=True
        )
        required = {"level", "page_num", "block_num", "par_num", "line_num", "conf", "text"}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError
        lines, words, previous = [], [], None
        weighted, length, text_length = 0.0, 0, 0
        for index, row in enumerate(rows):
            if index >= 25000 or None in row or any(row[key] is None for key in required):
                raise ValueError
            if int(row["level"]) != 5:
                continue
            word = row["text"].strip()
            if not word:
                continue
            confidence = float(row["conf"])
            if not math.isfinite(confidence) or not 0 <= confidence <= 100:
                raise ValueError
            # Be stricter on amounts/identifiers; even high confidence can be wrong.
            if any(char.isdigit() for char in word) and confidence < 85:
                raise DocumentError("ocr_unclear")
            position = tuple(
                int(row[key]) for key in ("page_num", "block_num", "par_num", "line_num")
            )
            if any(part < 1 for part in position):
                raise ValueError
            if previous is not None and position != previous:
                lines.append(" ".join(words))
                words = []
            words.append(word)
            previous = position
            text_length += len(word) + 1
            if text_length - 1 > MAX_TEXT:
                raise DocumentError("local_ocr_limit")
            weighted += len(word) * confidence
            length += len(word)
        if words:
            lines.append(" ".join(words))
        confidence = weighted / length / 100 if length else 0
        if confidence < 0.7:
            raise DocumentError("ocr_unclear")
        return Recognition("\n".join(lines), confidence)
    except (ValueError, KeyError, UnicodeError, csv.Error, OverflowError):
        raise DocumentError("ocr_unclear") from None
