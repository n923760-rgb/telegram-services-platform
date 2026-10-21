"""Source-bound page-transition fixtures shared by unit and native worker checks."""

from app.builders.schema import Document, Section


def boundary_document(lang="en", *, body="paragraph", blank=False, wrapped=False):
    heading = "SECTION 00123" if lang == "en" else "تفاصيل الطلب 00123"
    if wrapped:
        heading = (
            "Detailed source heading " if lang == "en" else "تفاصيل الطلب المهمة "
        ) * 6 + "00123"
    text = "First body 125.50 retained." if lang == "en" else "محتوى الطلب بمبلغ 125.50 ريال محفوظ."
    section = Section(heading=heading)
    if body == "bullet":
        section.bullets = [text]
    else:
        section.paragraphs = [("\n" if blank else "") + text]
    return Document(
        title="Pagination review" if lang == "en" else "مراجعة تنسيق المستند",
        sections=[Section(paragraphs=[f"Record {i:02d} retained." for i in range(20)]), section],
    )
