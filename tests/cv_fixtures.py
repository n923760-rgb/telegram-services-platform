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
