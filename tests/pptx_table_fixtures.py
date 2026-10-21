"""Synthetic source records for uneven-column native PowerPoint qualification."""


def table_slide(language, count=4):
    arabic = language == "ar"
    note = (
        "مراجعة بيانات الطلب والتأكد من مطابقة التفاصيل قبل تأكيد التسليم للعميل."
        if arabic
        else "Review order details and confirm the source records before customer delivery."
    )
    return {
        "title": "متابعة الطلبات" if arabic else "Order follow-up",
        "table": {
            "columns": ["الرقم", "الملاحظة", "المبلغ"] if arabic else ["ID", "Note", "Amount"],
            "rows": [[f"{index:05d}", note, "125.50"] for index in range(count)],
        },
    }
