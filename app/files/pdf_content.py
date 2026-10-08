"""Detect raster drawing instructions without decoding customer image pixels."""

from pypdf.generic import ContentStream, StreamObject


def has_image_content(page, reader):
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
