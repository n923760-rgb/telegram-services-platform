def inputs(language="ar"):
    if language == "en":
        return {
            "language": "en",
            "full_name": "Sam Example",
            "contact": "0500123456 | sample@example.invalid\nAbha | portfolio.example.invalid",
            "summary": "Operations coordinator with documented experience.",
            "experience": "Operations coordinator — Example Company\n2024-01-09 — 2026-10-09\nManaged 00123 records and 125.50 units in the sample project.",
            "education": "Diploma in administration — Example Institute\n2023",
            "skills": "Excel | Scheduling | Communication",
            "additional": "English and Arabic\nCertificate 00017",
        }
    return {
        "language": "ar",
        "full_name": "سام النموذجي",
        "contact": "0500123456 | sample@example.invalid\nأبها | portfolio.example.invalid",
        "summary": "منسق عمليات لديه خبرة موثقة في تنظيم الأعمال ومتابعة السجلات.",
        "experience": "منسق عمليات — شركة المثال\nمن 2024-01-09 إلى 2026-10-09\nمتابعة 00123 سجل و125.50 وحدة في مشروع تجريبي.",
        "education": "دبلوم إدارة — معهد المثال\n2023",
        "skills": "Excel | تنظيم المواعيد | التواصل",
        "additional": "العربية والإنجليزية\nالشهادة 00017",
    }


def revision(source=None, *, theme="modern", density="comfortable"):
    """Explicit model response fixture, never evidence of live AI translation quality."""
    from app.services.cv_formatting.schema import Inputs

    source = source or inputs()
    values = Inputs.parse(source)
    originals = values.segments()
    names = [name for name in values.ordered_names() if getattr(values, name)]
    if values.summary is None:
        names.insert(0, "summary")
    baseline = Inputs.parse(
        inputs("ar" if values.full_name == inputs()["full_name"] else "en")
    ).segments()
    bodies = []
    for language in values.targets():
        known = Inputs.parse(inputs(language)).segments()
        segments = []
        for key, item in originals.items():
            text = item["text"]
            other = known.get(key)
            # Translate only the reviewed default fixture; custom data stays literal.

            if other and key in baseline and baseline[key]["text"] == text:
                text = other["text"]
            if language == "en":
                text = {
                    "منسق عمليات": "Operations Coordinator",
                    "مشروع أرشفة السجلات 00001": "Records Archive Project 00001",
                    "تنظيم سجلات المشروع ومتابعة الأعمال.": "Organized project records and followed up on tasks.",
                }.get(text, text)
            name = item["field"]
            presentation = "paragraph"
            if name in {
                "experience",
                "education",
                "projects",
                "research",
                "publications",
            } and key.endswith(":1"):
                presentation = "lead"
            elif name in {"skills", "additional"} or (name == "experience" and key.endswith(":3")):
                presentation = "bullet"
            segments.append({"id": key, "text": text, "presentation": presentation})
        summary = None
        if values.summary is None:
            summary = {
                "text": "Administrative diploma holder with scheduling and spreadsheet skills."
                if language == "en"
                else "حاصل على دبلوم إدارة مع مهارات تنظيم المواعيد واستخدام الجداول.",
                "source_ids": ["education:1", "skills:1"],
            }
        bodies.append(
            {
                "language": language,
                "full_name": inputs(language)["full_name"]
                if values.full_name in {inputs()["full_name"], inputs("en")["full_name"]}
                else values.full_name,
                "segments": segments,
                "summary": summary,
            }
        )
    return {
        "design": {"theme": theme, "density": density},
        "section_order": names,
        "bodies": bodies,
    }


def planned(source=None, **design):
    from app.services.cv_formatting.schema import Inputs, document, revision_schema

    source = source or inputs()
    values = Inputs.parse(source)
    return document(values, revision_schema(values).model_validate(revision(source, **design)))
