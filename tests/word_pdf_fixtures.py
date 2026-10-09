import os
from pathlib import Path

from app.builders.word_schema import WordDocument
from app.providers.documents.libreoffice import LibreOfficeDocuments

TEXT = (
    "الطلب 00123 بتاريخ 2026-10-09 وقيمته 125.50 ريال\nInvoice 00123 Total 125.50 Date 2026-10-09"
)


def document():
    return WordDocument(title="تقرير الطلبات", sections=[{"paragraphs": TEXT.splitlines()}])


def renderer():
    binary = os.getenv("LOCAL_WORD_PDF_TEST_BINARY")
    return LibreOfficeDocuments(binary=Path(binary)) if binary else LibreOfficeDocuments()


def table_document():
    rows = [[f"{100 + index:05d}", "2026-10-09", "125.50"] for index in range(55)]
    return WordDocument(
        title="تقرير الطلبات",
        sections=[{"tables": [{"columns": ["الرقم", "التاريخ", "المبلغ"], "rows": rows}]}],
    )
