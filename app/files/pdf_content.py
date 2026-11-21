"""Inspect bounded PDF instructions before text-only conversion."""

import unicodedata

from pypdf.generic import ContentStream, DictionaryObject, NameObject, StreamObject

from app.services.base import ServiceError


def _has_marked_arabic(operands, resources):
    if len(operands) != 2:
        return False
    properties = operands[1]
    if isinstance(properties, NameObject):
        named = resources.get("/Properties")
        properties = named.get_object().get(properties) if named is not None else None
    if properties is not None:
        properties = properties.get_object()
    if not isinstance(properties, DictionaryObject):
        return False
    actual = properties.get("/ActualText")
    if actual is not None:
        actual = actual.get_object()
    return isinstance(actual, str) and any(
        unicodedata.category(char).startswith("M")
        and unicodedata.name(char, "").startswith("ARABIC ")
        for char in actual
    )


def has_image_content(page, reader, *, reject_marked_arabic=False):
    content = page.get_contents()
    if content is None:
        return False
    budget = 100000

    def visit(stream, resources, depth, ancestors):
        nonlocal budget
        if depth > 16 or id(stream) in ancestors:
            raise ValueError("unsupported PDF Form nesting")
        ancestors = ancestors | {id(stream)}
        if hasattr(resources, "get_object"):
            resources = resources.get_object()
        for operands, operator in stream.operations:
            budget -= 1
            if budget < 0:
                raise ValueError("PDF content inspection limit")
            if operator == b"INLINE IMAGE":
                return True
            if (
                reject_marked_arabic
                and operator == b"BDC"
                and _has_marked_arabic(operands, resources)
            ):
                # pypdf can emit the underlying glyph codes instead of the declared
                # replacement, corrupting Arabic letters with combining marks.
                raise ServiceError("pdf_text_marked_arabic")
            if operator != b"Do":
                continue
            if len(operands) != 1:
                raise ValueError("invalid PDF drawing instruction")
            objects = resources.get("/XObject", {})
            if hasattr(objects, "get_object"):
                objects = objects.get_object()
            target = objects[operands[0]].get_object()
            if not isinstance(target, StreamObject):
                raise ValueError("invalid PDF drawing object")
            subtype = target.get("/Subtype")
            if subtype == "/Image":
                return True
            if subtype != "/Form":
                raise ValueError("unsupported PDF drawing object")
            if id(target) in ancestors:
                raise ValueError("cyclic PDF Form")
            if visit(
                ContentStream(target, reader),
                target.get("/Resources", resources),
                depth + 1,
                ancestors | {id(target)},
            ):
                return True
        return False

    return visit(content, page.get("/Resources", {}), 0, set())
