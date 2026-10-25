"""Declared optional content requires visibility-aware processing."""

from pypdf import PdfReader


def has_layer_declaration(reader: PdfReader) -> bool:
    # Empty and indirect declarations are still unsupported configurations.
    return reader.trailer["/Root"].get("/OCProperties") is not None
