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


def wide_table_document(*, arabic=False, design="modern"):
    columns = (
        [
            "المرجع",
            "وصف حالة التسليم الحالية",
            "الإدارة المسؤولة",
            "تاريخ التسليم",
            "المبلغ",
            "معلومات التسليم الإضافية",
        ]
        if arabic
        else [
            "Reference",
            "Description of the current delivery status",
            "Responsible department",
            "Delivery date",
            "Amount",
            "Additional delivery information",
        ]
    )
    rows = [
        [
            f"{100 + index:05d}",
            "متابعة تشغيلية مفصلة للتسليم المطلوب"
            if arabic
            else "Detailed operational follow up for the requested delivery",
            "إدارة العمليات" if arabic else "Operations department",
            "2026-10-25",
            "125.50 SAR",
            "لم تعتمد الدفعة" if arabic else "No payment approved",
        ]
        for index in range(35)
    ]
    return WordDocument(
        title="سجل المتابعة" if arabic else "Delivery follow up",
        design={"theme": design},
        sections=[{"tables": [{"columns": columns, "rows": rows}]}],
    )
