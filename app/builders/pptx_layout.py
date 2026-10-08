"""Bounded font-metric layout planning, separate from native PPTX serialization.

Measurement includes conservative width/height slack. It is not a substitute for
rendering in Microsoft PowerPoint, especially when the chosen font is substituted.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

from PIL import ImageFont

FONT = "DejaVu Sans"
BODY_WIDTH = 11.6 * 72
BODY_HEIGHT = 4.85 * 72
FRAME_MARGIN = 0.1 * 72


@lru_cache(maxsize=16)
def _font(size, bold=False):
    # The same fonts-dejavu-core package is required by Docker and hosted CI.
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(filename, size=size * 4)


def wrapped_lines(text, size, width, *, bold=False):
    font = _font(size, bold)
    available = (width - 2 * FRAME_MARGIN) * 0.88
    if available <= 0:
        raise ValueError("invalid text width")
    count = 0
    for explicit_line in text.split("\n"):
        current = ""
        count += 1
        for token in re.findall(r"\S+|\s+", explicit_line):
            if font.getlength(current + token) / 4 <= available:
                current += token
                continue
            if current.strip():
                count += 1
                current = ""
            token = token.lstrip()
            for character in token:
                if font.getlength(current + character) / 4 > available:
                    count += 1
                    current = ""
                current += character
    return count


def text_height(texts, size, width, *, bold=False, gap=10):
    lines = sum(wrapped_lines(text, size, width, bold=bold) for text in texts)
    return lines * size * 1.2 + max(0, len(texts) - 1) * gap + 2 * FRAME_MARGIN + 8


@dataclass(frozen=True)
class Layout:
    kind: str
    title_size: int
    body_size: int
    row_heights: tuple[float, ...] = ()


def plan_slide(item, *, cover_candidate=False):
    table = getattr(item, "table", None)
    if cover_candidate and table is None and len(item.bullets) <= 2:
        if (
            text_height([item.title], 42, BODY_WIDTH, bold=True) <= 1.6 * 72
            and text_height(item.bullets, 24, BODY_WIDTH) <= 1.9 * 72
        ):
            return Layout("cover", 42, 24)
    if text_height([item.title], 32, BODY_WIDTH, bold=True) > 1.3 * 72:
        raise ValueError("slide title too dense; use a concise source-bound title")
    if table is not None:
        width = BODY_WIDTH / len(table.columns)
        heights = tuple(
            max(
                40,
                max(wrapped_lines(cell, size, width, bold=index == 0) for cell in row) * size * 1.2
                + 16,
            )
            for index, row in enumerate([table.columns, *table.rows])
            for size in [21 if index == 0 else 20]
        )
        if sum(heights) > BODY_HEIGHT:
            raise ValueError("slide table too dense; split records across planned slides")
        return Layout("table", 32, 20, heights)
    for size in (26, 24, 22, 20):
        if text_height(item.bullets, size, BODY_WIDTH - 24) <= BODY_HEIGHT:
            return Layout("content", 32, size)
    raise ValueError("slide body too dense; split source content across planned slides")
