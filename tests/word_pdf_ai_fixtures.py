from app.services.text_to_word_pdf.schema import Inputs


def inputs(language="ar"):
    text = (
        "نطلب مراجعة الطلب 00123 بتاريخ 2026-10-14.\n"
        "المبلغ 125.50 ريال ولم تتم الموافقة على الصرف.\n"
        "التواصل 0500123456 وsample@example.invalid.\n"
        "يعتمد التنفيذ على استكمال المراجعة والحصول على موافقة المسؤول."
        if language == "ar"
        else "Please review request 00123 dated 2026-10-14.\n"
        "The amount is 125.50 SAR and payment has not been approved.\n"
        "Contact 0500123456 or sample@example.invalid.\n"
        "Execution depends on completing the review and obtaining the owner's approval."
    )
    return {"text": text, "mode": "smart"}


def revision(source=None, theme="classic"):
    values = Inputs.parse(source or inputs())
    return {
        "title": values.title or ("مراجعة الطلب" if "نطلب" in values.text else "Request review"),
        "design": {"theme": theme, "density": "comfortable"},
        "sections": [
            {
                "heading": "تفاصيل الطلب" if "نطلب" in values.text else "Request details",
                "segments": [
                    {"id": i, "text": line, "kind": "paragraph" if i == 1 else "bullet"}
                    for i, line in enumerate(values.lines(), 1)
                ],
            }
        ],
    }
