def inputs(language="ar", whitespace="trim"):
    headers = "المعرف,العميل,المبلغ,التاريخ" if language == "ar" else "ID,Customer,Amount,Date"
    return {
        "language": language,
        "delimiter": "comma",
        "whitespace": whitespace,
        "text": headers
        + "\n00123, أحمد ,125.50,2026-10-09\n00124,,0,\n00123,أحمد,125.50,2026-10-09\n00017,=1+1,000.00,08/10/2026",
    }
