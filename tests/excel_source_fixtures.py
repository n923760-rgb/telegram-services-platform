from app.builders.schema import Table


def typed_table():
    return Table.model_validate(
        {
            "title": "سجل الطلبات",
            "columns": ["المعرّف", "العميل", "المبلغ (ريال)", "التاريخ", "النسبة", "مؤكد"],
            "column_formats": [
                {"kind": kind} for kind in ("text", "text", "number", "date", "percent", "boolean")
            ],
            "rows": [
                ["00123", "أحمد", 125.5, "2026-10-08", 0.125, True],
                ["00124", "Example", 0, None, 0, False],
                ["00123", "أحمد", 125.5, "2026-10-08", 0.125, True],
            ],
        }
    )


def inputs(language="ar"):
    first = (
        "00123 | أحمد | 125.50 | 2026/10/08 | 12.5% | نعم"
        if language == "ar"
        else "00123 | Ahmed | 125.50 | 2026/10/08 | 12.5% | yes"
    )
    second = (
        "00124 | Example | 0 | 0% | لا" if language == "ar" else "00124 | Example | 0 | 0% | no"
    )
    return {"target": "excel", "text": "\n".join([first, second, first])}


def plan(language="ar"):
    first = [
        "00123",
        "أحمد" if language == "ar" else "Ahmed",
        "125.50",
        "2026/10/08",
        "12.5%",
        "نعم" if language == "ar" else "yes",
    ]
    table = typed_table().model_dump(mode="json")
    if language == "en":
        table["title"] = "Order register"
        table["columns"] = ["ID", "Customer", "Amount (SAR)", "Date", "Rate", "Confirmed"]
        table["rows"][0][1] = table["rows"][2][1] = "Ahmed"
    return {
        "table": table,
        "evidence": [
            {"source_id": i, "quotes": quotes}
            for i, quotes in enumerate(
                [
                    first,
                    ["00124", "Example", "0", None, "0%", "لا" if language == "ar" else "no"],
                    first,
                ],
                1,
            )
        ],
        "context_ids": [],
    }
