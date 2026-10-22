"""Structural delivery gate for locally generated artifacts, not visual acceptance.

Do not use this lightweight check as an uploaded-document security boundary.
"""

from io import BytesIO
from typing import Literal
from zipfile import BadZipFile, ZipFile

from lxml import etree
from pypdf import PdfReader
from pypdf.errors import PdfReadError

Kind = Literal["docx", "xlsx", "pptx", "pdf"]
ROOTS = {
    "docx": (
        "word/document.xml",
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document",
    ),
    "xlsx": (
        "xl/workbook.xml",
        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}workbook",
    ),
    "pptx": (
        "ppt/presentation.xml",
        "{http://schemas.openxmlformats.org/presentationml/2006/main}presentation",
    ),
}


def validate(data: bytes, kind: Kind) -> bytes:
    """Fail closed before storage/delivery; error text contains no customer content."""
    try:
        if not data or len(data) > 10 * 1024 * 1024:
            raise ValueError
        if kind == "pdf":
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted or not reader.pages:
                raise ValueError
            # Access the full page tree, not only the header signature.
            for page in reader.pages:
                if page.mediabox.width <= 0 or page.mediabox.height <= 0:
                    raise ValueError
        else:
            path, tag = ROOTS[kind]
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                names = [entry.filename for entry in entries]
                if (
                    len(names) != len(set(names))
                    or len(names) > 2000
                    or sum(entry.file_size for entry in entries) > 40 * 1024 * 1024
                    or not {path, "[Content_Types].xml", "_rels/.rels"} <= set(names)
                ):
                    raise ValueError
                parser = etree.XMLParser(resolve_entities=False, no_network=True)
                for name in names:
                    if name.endswith((".xml", ".rels")):
                        node = etree.fromstring(archive.read(name), parser)
                        if name == path and node.tag != tag:
                            raise ValueError
                if archive.testzip() is not None:
                    raise ValueError
    except (ValueError, KeyError, BadZipFile, etree.XMLSyntaxError, PdfReadError) as exc:
        raise ValueError("generated artifact failed structural validation") from exc
    return data
