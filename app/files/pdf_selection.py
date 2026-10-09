"""Bounded one-based page selection in the customer's requested order."""

import re


def page_selection(value: str) -> list[int]:
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        raise ValueError("invalid PDF page selection")
    pages = []
    for item in value.replace("،", ",").split(","):
        if not re.fullmatch(r"\s*\d{1,3}(?:\s*-\s*\d{1,3})?\s*", item):
            raise ValueError("invalid PDF page selection")
        ends = [int(number.strip()) for number in item.split("-")]
        first, last = ends[0], ends[-1]
        if not 1 <= first <= last <= 200 or len(pages) + last - first + 1 > 200:
            raise ValueError("invalid PDF page selection")
        pages.extend(range(first, last + 1))
    if len(set(pages)) != len(pages):
        raise ValueError("duplicate PDF page selection")
    return pages
