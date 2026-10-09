def inputs(language="ar"):
    notes = (
        "Discussed order 00123 worth 125.50.\n"
        "Approved project start on 2026-10-09.\n"
        "Sam to send report 00017 on 2026-10-12.\n"
        "Review possible budget change."
    )
    if language == "ar":
        notes = (
            "نوقش الطلب 00123 بقيمة 125.50 ريال.\n"
            "اعتمد بدء المشروع بتاريخ 2026-10-09.\n"
            "سام يرسل التقرير 00017 بتاريخ 2026-10-12.\n"
            "تحتاج مقترحات الميزانية إلى مراجعة."
        )
    return {
        "title": "Meeting 2026-10-09" if language == "en" else "اجتماع 2026-10-09",
        "language": language,
        "notes": notes,
    }


def plan():
    return {
        "assignments": [
            {"note_id": 1, "category": "discussion"},
            {"note_id": 2, "category": "decision"},
            {"note_id": 3, "category": "action"},
            {"note_id": 4, "category": "review"},
        ]
    }
