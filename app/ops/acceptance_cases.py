"""Synthetic acceptance data only; no customer uploads or test-suite imports."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.services.base import InputSchema, ServiceError
from app.services.registry import registry

OWNER = 424242424242


@dataclass(frozen=True)
class Case:
    name: str
    slug: str
    inputs: dict
    tokens: tuple[str, ...] = ()
    pdf_pages: int = 1


def picture(*, shaded=False, mixed=False):
    image = Image.new("RGB", (1400, 700), "white")
    draw = ImageDraw.Draw(image)
    if shaded:
        for x in range(image.width):
            value = 125 + x * 100 // image.width
            draw.line((x, 0, x, image.height), fill=(value, value, value))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    text = "Invoice 00123\nTotal 125.50\nDate 2026-10-15"
    if mixed:
        text = "مرحبا بكم\n" + text
    draw.multiline_text((100, 80), text, fill="black", font=font, spacing=24)
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def source_pdf():
    if "Acceptance" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("Acceptance", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        )
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(600, 800))
    pdf.setFont("Acceptance", 12)
    rows = [["ID", "Amount", "Note"], ["00123", "125.50", "Example"], ["00017", "0", "Pending"]]
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            pdf.drawString(60 + c * 160, 710 - r * 35, text)
    for x in (45, 205, 365, 525):
        pdf.line(x, 725, x, 620)
    for y in (725, 690, 655, 620):
        pdf.line(45, y, 525, y)
    pdf.save()
    return output.getvalue()


def cases(assets):
    pdf, image, shaded, mixed = (assets[key] for key in ("pdf", "image", "shaded", "mixed"))
    text = "Order 00123\nAmount 125.50 SAR\nThe payment has not been approved."
    cv = {
        "language": "bilingual",
        "cv_type": "professional",
        "full_name": "سامي المثال",
        "headline": "منسق عمليات",
        "contact": "0500123456 | demo@example.invalid",
        "experience": "تنسيق العمليات لدى شركة المثال منذ 2024.\nمتابعة سجلات الأعمال وتنظيم المواعيد.",
        "education": "دبلوم إدارة أعمال من معهد المثال، 2023.",
        "skills": "Excel | تنظيم المواعيد | التواصل",
    }
    result = [
        Case(
            "csv",
            "csv_review",
            {
                "language": "en",
                "delimiter": "comma",
                "whitespace": "trim",
                "text": "ID,Name,Amount\n00123, Demo ,125.50\n00017,=1+1,0\n00123,Demo,125.50",
            },
            ("00123",),
        ),
        *[
            Case(
                "cv_" + lang,
                "cv_formatting",
                cv | {"language": lang},
                ("0500123456",),
                2 if lang == "bilingual" else 1,
            )
            for lang in ("ar", "en", "bilingual")
        ],
        Case("enhance", "document_image_enhancement", {"image": shaded}),
        Case("ocr_en", "image_to_text", {"images": [image]}, ("00123", "125.50")),
        Case("ocr_mixed", "image_to_text", {"images": [mixed]}, ("00123", "125.50")),
        Case(
            "images_pdf",
            "images_to_pdf",
            {"images": [image, mixed], "orientation": "auto"},
            pdf_pages=2,
        ),
        *[
            Case(
                "minutes_" + lang,
                "meeting_minutes",
                {
                    "language": lang,
                    "title": "Meeting 2026-10-15",
                    "notes": "Discussed order 00123.\nApproved project start.\nSam must send report 00017 on 2026-10-20.",
                },
                ("00123", "00017"),
            )
            for lang in ("ar", "en")
        ],
        *[
            Case(
                "tables_" + mode,
                "pdf_tables_excel",
                {"pdf": pdf, "mode": mode, "language": "en"},
                ("00123",),
            )
            for mode in ("direct", "labels")
        ],
        Case("pdf_word", "pdf_to_word", {"pdf": pdf}, ("00123",)),
        Case(
            "pdf_extract",
            "pdf_tools",
            {"files": [pdf], "operation": "extract", "pages": "1"},
            ("00123",),
        ),
        Case(
            "pdf_merge",
            "pdf_tools",
            {"files": [pdf, assets["pdf2"]], "operation": "merge"},
            ("00123",),
            2,
        ),
        *[
            Case(
                "editing_" + mode,
                "text_editing",
                {"text": text, "mode": mode, **({"tone": "formal"} if mode == "rewrite" else {})},
                ("00123",),
            )
            for mode in ("proofread", "rewrite")
        ],
        Case("summary", "text_summary", {"text": text, "language": "en", "length": "short"}),
        Case(
            "word_direct",
            "text_to_office",
            {"text": text, "target": "word", "mode": "direct"},
            ("00123",),
        ),
        Case(
            "word_smart",
            "text_to_office",
            {"text": text, "target": "word", "mode": "smart"},
            ("00123",),
        ),
        Case(
            "excel_smart",
            "text_to_office",
            {"text": "00123 | Demo | 125.50\n00017 | Example | 0", "target": "excel"},
            ("00123",),
        ),
        *[
            Case("text_pdf_" + mode, "text_to_pdf", {"text": text, "mode": mode}, ("00123",))
            for mode in ("direct", "smart")
        ],
        Case("pptx", "text_to_pptx", {"text": text}),
        *[
            Case("word_pdf_" + mode, "text_to_word_pdf", {"text": text, "mode": mode}, ("00123",))
            for mode in ("direct", "smart")
        ],
        *[
            Case(
                "translation_" + lang,
                "text_translation",
                {"text": text, "language": lang, "style": "formal"},
                ("00123",),
            )
            for lang in ("ar", "en")
        ],
    ]
    from app.ops.service_portfolio import customer_slugs

    if {case.slug for case in result} != set(customer_slugs()):
        raise ValueError("Acceptance cases must cover the exact public portfolio")
    if len({case.name for case in result}) != len(result):
        raise ValueError("Duplicate acceptance case")
    for case in result:
        plugin = registry.types[case.slug]
        try:
            InputSchema.model_validate(plugin.input_schema).validate_inputs(case.inputs)
            plugin.needs_ai(case.inputs)
        except (ServiceError, ValueError):
            raise ValueError("Invalid acceptance fixture: " + case.name) from None
    return result
