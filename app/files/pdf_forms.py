"""Shared conservative boundary for PDF operations that cannot preserve forms."""

from pypdf import PdfReader
from pypdf._page import PageObject


def has_form_declaration(reader: PdfReader) -> bool:
    # Empty declarations are still unsupported; truthiness loses that signal.
    root = reader.trailer["/Root"]
    return root.get("/AcroForm") is not None or root.get("/Perms") is not None


def has_widget(page: PageObject) -> bool:
    annotations = page.get("/Annots")
    # Malformed inspected objects deliberately propagate to caller's file_invalid.
    return annotations is not None and any(
        annotation.get_object()["/Subtype"] == "/Widget" for annotation in annotations.get_object()
    )


def has_interactive_content(reader: PdfReader) -> bool:
    return has_form_declaration(reader) or any(has_widget(page) for page in reader.pages)
