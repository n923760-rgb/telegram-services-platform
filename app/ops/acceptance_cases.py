"""Synthetic acceptance data only; no customer uploads or test-suite imports."""

from dataclasses import dataclass, replace
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
    exact_pdf_pages: int | None = None
    pdf_rotations: tuple[int, ...] = ()
    pptx_slides: int | None = None
    required_sheets: tuple[str, ...] = ()
    expected_files: tuple[str, ...] | None = None
    pdf_page_tokens: tuple[tuple[str, ...], ...] = ()
    pdf_image_sources: tuple[str, ...] = ()
    pdf_image_hashes: tuple[str, ...] = ()
    changed_text_files: tuple[str, ...] = ()
    review_checks: tuple[str, ...] = ()
    docx_tables: tuple[tuple[tuple[str, ...], ...], ...] = ()
    pdf_links: tuple[str, ...] = ()
    docx_text_counts: tuple[tuple[str, int], ...] = ()


def representative_cases(result):
    """Strengthen existing cases without increasing the live run/call allowance."""
    proofreading = (
        "The report contain several error and need a careful review.\n"
        "Order 00123 have not been approved for payment of 125.50 SAR.\n"
        "Please sends the corrected copy to demo@example.invalid before 2026-10-30."
    )
    rewrite = (
        "يا فريق، الكلام في التقرير مبعثر ونحتاج نخليه واضح قبل ما نرسله للإدارة.\n"
        "الطلب 00123 بمبلغ 125.50 SAR ما اعتمدناه، ولا ترسلونه للمحاسبة على أنه معتمد.\n"
        "رتبوا النسخة وأرسلوها إلى demo@example.invalid قبل 2026-10-30 بدون إضافة وعود جديدة."
    )
    arabic_translation = (
        "لم تعتمد اللجنة دفع مبلغ 125.50 SAR للطلب 00123، ولم ترفض الطلب نهائيا.\n"
        "يجب إرسال المستند الناقص إلى demo@example.invalid قبل 2026-10-30.\n"
        "لا يبدأ التنفيذ إلا بعد موافقة مكتوبة؛ الموعد المقترح ليس التزاما بالتسليم."
    )
    summary = "\n".join(
        [
            "The operations committee reviewed order 00123 for 125.50 SAR and did not approve payment because the supporting receipt was missing.",
            "The request remains open for review; the committee did not reject the order permanently and did not authorize delivery.",
            "Sam must send the missing receipt to demo@example.invalid before 2026-10-30. The finance team will then check it before any approval decision.",
            "A proposed delivery date of 2026-11-02 is provisional. It must not be described as a confirmed commitment to the customer.",
            "The warehouse reported that the requested items were available at the time of the meeting, but no stock reservation was approved.",
            "The team discussed using a shorter internal form to reduce repeated data entry. This was a suggestion rather than an approved process change.",
            "The current form asks staff to record the customer reference, attach the receipt, and identify the person responsible for the next review.",
            "Several staff members described delays caused by unclear handovers. Their examples were background discussion and introduced no new deadlines.",
            "The support team requested clearer messages when a document is missing, so customers can distinguish a pending request from a rejected one.",
            "The committee agreed that status messages must reflect the actual decision. A request for more information must not be presented as payment approval.",
            "The meeting also covered the layout of internal reports. No purchase of software, extra staffing, or budget increase was approved.",
            "At the close of the meeting, the payment remained unapproved. The immediate next action was to obtain the receipt and return it for finance review.",
        ]
    )
    document = "\n\n".join(
        f"SEC-{number:02d}: "
        "The operations team records each handover before sending the file for review. "
        "A missing receipt keeps the request pending; availability alone does not authorize delivery. "
        "Order 00123 remains unapproved for payment of 125.50 SAR.\n"
        "يراجع الفريق المستندات قبل إحالة الطلب للاعتماد، ويحفظ مسؤول المتابعة الملاحظات في السجل. "
        "وجود الأصناف لا يعني الموافقة على التسليم، ولا يجوز تحويل الموعد المقترح إلى وعد مؤكد."
        for number in range(1, 13)
    )
    arabic_document = "\n".join(
        [
            "محضر متابعة الطلب",
            "الطلب 00123 بمبلغ 125.50 SAR لم تعتمد اللجنة دفعه ولم ترفضه نهائيا.",
            "التقرير 00017 مطلوب لاستكمال المراجعة، ويبقى الطلب معلقا حتى استلامه.",
            "اقترح خالد التسليم في 2026-11-20 دون اعتماد الموعد أو تقديم التزام للعميل.",
            "المتاح 40 قطعة، منها 12 قطعة جاهزة للفحص و28 قطعة قيد المراجعة.",
            "لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها.",
            "المطلوب",
            "يجب على سامي إرسال التقرير إلى demo@example.invalid قبل 2026-11-18.",
            "نوقش تبسيط نموذج المتابعة دون اعتماد تغيير أو زيادة الميزانية.",
        ]
    )
    formatting_notes = "نسّق بعناوين واضحة وفقرات قصيرة، ولا تعرض تعليمات التنسيق في المستند."
    overrides = {
        "editing_proofread": {
            "text": proofreading,
            "checks": (
                "Correct the actual English grammar errors; preserve negation, amounts, contacts and deadline.",
            ),
        },
        "editing_rewrite": {
            "text": rewrite,
            "checks": (
                "Rewrite colloquial Arabic in formal prose; preserve the unapproved status and add no promises.",
            ),
        },
        "translation_en": {
            "text": arabic_translation,
            "checks": (
                "Translate Arabic prose into English; distinguish not approved from permanently rejected and proposed from confirmed.",
            ),
        },
        "translation_ar": {
            "text": "Order 00123\nAmount 125.50 SAR\nThe payment has not been approved.",
            "checks": (
                "Translate English prose into Arabic; preserve the unapproved payment status and exact source values.",
            ),
        },
        "summary": {
            "text": summary,
            "checks": (
                "Compress twelve paragraphs to at most three grounded points; retain the payment decision, next action and provisional delivery status.",
            ),
        },
        "word_pdf_direct": {
            "text": document,
            "checks": (
                "Inspect every PDF page for clipping and Arabic/English reading order; compare editable Word with the full source.",
            ),
        },
    }
    arabic_minutes = "\n".join(
        [
            "ناقش الفريق الطلب 00123 بمبلغ 125.50 SAR.",
            "لم تعتمد اللجنة دفع المبلغ ولم ترفض الطلب نهائيا.",
            "اقترح خالد التسليم في 2026-11-20 دون اعتماد الموعد.",
            "قررت اللجنة إبقاء الطلب معلقا حتى استكمال المستندات.",
            "يجب على سامي إرسال التقرير 00017 إلى demo@example.invalid قبل 2026-11-18.",
            "نوقش تحسين نموذج المتابعة دون تحديد مسؤول أو موعد للتنفيذ.",
        ]
    )
    arabic_deck = "\n\n".join(
        [
            "مراجعة جاهزية التشغيل: يناقش الفريق حالة الطلبات وتسليم المستندات وجودة رسائل المتابعة. الهدف عرض الوضع الفعلي دون تقديم وعود غير معتمدة، وتوضيح ما تقرر وما بقي اقتراحا وما يتطلب إجراء لاحقا.",
            "حالة الدفع: الطلب 00123 بقيمة 125.50 ريال ما زال قيد المراجعة بسبب نقص الإيصال. لم تعتمد اللجنة الدفع ولم ترفض الطلب نهائيا. لا يجوز وصف طلب المستند الناقص بأنه موافقة، ولا يبدأ التنفيذ قبل موافقة مكتوبة.",
            "موعد التسليم: اقترح خالد التسليم في 2026-11-20، لكن اللجنة لم تعتمد هذا الموعد. يجب توضيح أنه موعد مقترح لا التزام مؤكد، ولا يملك فريق الدعم تأكيده للعميل قبل اكتمال المراجعة.",
            "حالة المخزون: المتاح في المستودع 40 قطعة، منها 12 قطعة جاهزة للفحص و28 قطعة تنتظر المراجعة. هذه الأعداد تصف حالة المخزون وقت الاجتماع فقط؛ لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها.",
            "المهمة التالية: سامي مسؤول عن إرسال التقرير 00017 والإيصال الناقص إلى demo@example.invalid قبل 2026-11-18. بعد استلام المستندات يراجعها فريق المالية، ثم يصدر قرار الاعتماد. إرسال التقرير وحده لا يعني الموافقة على الدفع.",
            "القرار المعتمد: اتفقت اللجنة على إبقاء الطلب معلقا حتى استكمال المستندات، وعلى أن تميز رسائل المتابعة بين قيد المراجعة ومرفوض ومعتمد. تحفظ الملاحظات في السجل ويطابق الموظف الرسالة مع آخر قرار مسجل قبل إرسالها.",
            "الاقتراحات والحدود: نوقش تبسيط نموذج المتابعة لتقليل تكرار إدخال البيانات، لكنه اقتراح لم يعتمد. لم توافق اللجنة على شراء برنامج أو زيادة الميزانية أو تعيين موظفين. لا تضاف توصيات أو مؤشرات أداء أو نتائج غير واردة في هذه الملاحظات.",
        ]
    )
    strengthened = []
    for case in result:
        override = overrides.get(case.name)
        if override:
            case = replace(
                case,
                inputs=case.inputs | {"text": override["text"]},
                review_checks=override["checks"],
            )
            if case.name.startswith("editing_"):
                case = replace(case, changed_text_files=("revision.txt",))
            elif case.name.startswith("translation_"):
                case = replace(case, changed_text_files=("translation.txt",))
            elif case.name == "word_pdf_direct":
                case = replace(
                    case,
                    pdf_pages=2,
                    tokens=tuple(f"SEC-{n:02d}" for n in range(1, 13)) + ("00123", "125.50"),
                )
        if case.name == "word_pdf_smart":
            case = replace(
                case,
                inputs=case.inputs
                | {
                    "text": arabic_document,
                    "title": "محضر متابعة الطلب",
                    "formatting_notes": formatting_notes,
                },
                tokens=(
                    "00123",
                    "125.50",
                    "00017",
                    "2026-11-20",
                    "2026-11-18",
                    "40",
                    "12",
                    "28",
                    "demo@example.invalid",
                ),
                docx_text_counts=(
                    ("محضر متابعة الطلب", 1),
                    ("المطلوب", 1),
                    (formatting_notes, 0),
                ),
                review_checks=(
                    "Inspect Word and every PDF page: title and source label appear once; Arabic reading order is correct without clipping or overlap.",
                    "Formatting notes guide layout only; no instruction text or paraphrase belongs in document content.",
                    "Preserve all source units, leading zeros and monetary precision; do not omit the final discussion note.",
                    "Keep payment unapproved and the request pending; Khalid's delivery proposal is not a commitment.",
                    "Keep inventory states distinct and preserve the lack of reservation or delivery authorization.",
                    "Sami owns the report action with deadline 2026-11-18; do not assign him Khalid's proposal date.",
                ),
            )
        if case.name == "minutes_ar":
            case = replace(
                case,
                inputs=case.inputs | {"notes": arabic_minutes},
                tokens=(
                    "00123",
                    "125.50",
                    "00017",
                    "2026-11-20",
                    "2026-11-18",
                    "demo@example.invalid",
                ),
                review_checks=(
                    "Inspect actual Arabic notes in Word and PDF; retain all source units and leading zeros.",
                    "Keep payment unapproved and the request pending, not permanently rejected.",
                    "Do not promote Khalid's proposed delivery date to an approved deadline or make him the task owner.",
                    "The explicit action belongs to Sami with deadline 2026-11-18; do not invent metadata for the final discussion note.",
                ),
            )
        if case.name == "pptx":
            case = replace(
                case,
                inputs={"text": arabic_deck, "slide_count": "7"},
                pptx_slides=7,
                tokens=(
                    "00123",
                    "125.50",
                    "00017",
                    "2026-11-20",
                    "2026-11-18",
                    "40",
                    "12",
                    "28",
                    "demo@example.invalid",
                    "لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها",
                ),
                review_checks=(
                    "Inspect all seven slides in native presentation rendering: Arabic reading order, readable text, no clipping or overlap.",
                    "Retain unapproved payment, pending request and the provisional delivery date; do not turn proposals into commitments.",
                    "Keep inventory counts tied to their original states without inventing reservation, delivery permission or new metrics.",
                    "Keep Sami's report, email and deadline distinct from Khalid's delivery proposal; preserve identifiers and monetary precision.",
                    "Use concise source-grounded slides without repetitive filler; retain the approved decision and unapproved process/budget proposals.",
                ),
            )
        strengthened.append(case)
    return strengthened


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


def source_pdf(*, second=False):
    if "Acceptance" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont("Acceptance", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        )
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(600, 800))
    pdf.setFont("Acceptance", 12)
    rows = [["ID", "Amount", "Note"], ["00123", "125.50", "Example"], ["00017", "0", "Pending"]]
    if second:
        rows = [["ID", "Amount", "Note"], ["00999", "80.00", "Second"], ["00018", "0", "Pending"]]
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
            required_sheets=("Data", "Source", "Review", "Columns"),
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
            {"images": [image, mixed], "orientation": "auto", "page_order": "٢، ١"},
            pdf_pages=2,
            exact_pdf_pages=2,
            pdf_image_sources=("mixed", "image"),
        ),
        *[
            Case(
                "minutes_" + lang,
                "meeting_minutes",
                {
                    "language": lang,
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
        Case(
            "pdf_word",
            "pdf_to_word",
            {"pdf": pdf},
            ("00123",),
            docx_tables=(
                (
                    ("ID", "Amount", "Note"),
                    ("00123", "125.50", "Example"),
                    ("00017", "0", "Pending"),
                ),
            ),
        ),
        Case(
            "pdf_extract",
            "pdf_tools",
            {"files": [pdf], "operation": "extract", "pages": "1"},
            ("00123",),
            exact_pdf_pages=1,
        ),
        Case(
            "pdf_rotate",
            "pdf_tools",
            {"files": [pdf], "operation": "rotate", "pages": "1", "rotation": "90"},
            ("00123",),
            exact_pdf_pages=1,
            pdf_rotations=(90,),
        ),
        Case(
            "pdf_merge",
            "pdf_tools",
            {"files": [pdf, assets["pdf2"]], "operation": "merge"},
            ("00123",),
            2,
            exact_pdf_pages=2,
            pdf_page_tokens=(("00123", "125.50"), ("00999", "80.00")),
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
            {"text": text, "target": "word"},
            ("00123",),
        ),
        Case(
            "excel_smart",
            "text_to_office",
            {"text": "00123 | Demo | 125.50\n00017 | Example | 0", "target": "excel"},
            ("00123",),
        ),
        *[
            Case(
                "text_pdf_" + mode,
                "text_to_pdf",
                {"text": text, **({"mode": mode} if mode == "direct" else {})},
                ("00123",),
            )
            for mode in ("direct", "smart")
        ],
        Case(
            "pptx",
            "text_to_pptx",
            {"text": text, "slide_count": "3"},
            ("00123", "125.50"),
            pptx_slides=3,
        ),
        *[
            Case(
                "word_pdf_" + mode,
                "text_to_word_pdf",
                {
                    "text": text,
                    "output_format": "both",
                    **({"mode": mode} if mode == "direct" else {}),
                },
                ("00123",),
            )
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
    result.append(
        Case(
            "business_card",
            "interactive_card",
            {
                "mode": "direct",
                "language": "en",
                "name": "Demo 00123",
                "links": "Website | https://example.invalid/",
            },
            ("00123",),
            exact_pdf_pages=1,
        )
    )
    result.append(
        Case(
            "qr_sheet",
            "qr_codes",
            {"language": "en", "entries": "Item 00123|https://example.invalid/?id=00123"},
            ("00123",),
            exact_pdf_pages=1,
        )
    )
    for language, brief in (
        (
            "ar",
            "أنا فني صيانة طائرات. أريد تصميمًا رسميًا بالبنفسجي الداكن، ومعلومات التواصل هي الأهم.",
        ),
        (
            "en",
            "I am a music teacher. Use a warm dark orange accent, a simple header and a compact button grid. Prioritize my lessons link.",
        ),
    ):
        social = "https://www.instagram.com/" if language == "ar" else "https://www.youtube.com/"
        other = (
            "https://example.invalid/contact"
            if language == "ar"
            else "https://example.invalid/lessons?id=00123"
        )
        label = "Contact" if language == "ar" else "Lessons"
        result.append(
            Case(
                "business_card_smart_" + language,
                "interactive_card",
                {
                    "mode": "smart",
                    "language": language,
                    "name": "Demo 00123",
                    "profile": brief,
                    "phone": "0501234567",
                    "links": social + "\n" + label + "|" + other,
                },
                ("00123",),
                exact_pdf_pages=1,
                pdf_links=(
                    social,
                    other,
                    "https://wa.me/966501234567",
                ),
                review_checks=(
                    "Inspect the PDF on mobile: readable header, exact names and every clickable target.",
                    "Compare color, hierarchy and layout with the free-form brief; record mismatches before activation.",
                    "Confirm the named social-platform button opens the exact supplied destination; no account ownership claim.",
                    "Confirm the run records real provider calls and calculated cost; native output is not AI qualification.",
                ),
            )
        )
    # Exact customer deliverables for these bounded synthetic fixtures. This is
    # acceptance metadata, not production service dispatch or payment policy.
    deliverables = {
        "business_card": ("business-card.pdf",),
        "business_card_smart_ar": ("business-card.pdf",),
        "business_card_smart_en": ("business-card.pdf",),
        "qr_sheet": ("qr-codes.pdf",),
        "csv": ("review.xlsx",),
        "enhance": ("enhanced.png", "comparison.png", "received.png"),
        "ocr_en": ("response.txt", "result.txt"),
        "ocr_mixed": ("response.txt", "result.txt"),
        "images_pdf": ("images.pdf",),
        "tables_direct": ("tables.xlsx",),
        "tables_labels": ("tables.xlsx",),
        "pdf_word": ("result.docx",),
        "pdf_extract": ("result.pdf",),
        "pdf_rotate": ("result.pdf",),
        "pdf_merge": ("result.pdf",),
        "summary": ("summary-source.txt", "response.txt"),
        "word_direct": ("result.docx",),
        "word_smart": ("result.docx",),
        "excel_smart": ("result.xlsx",),
        "text_pdf_direct": ("result.pdf",),
        "text_pdf_smart": ("result.pdf",),
        "pptx": ("result.pptx",),
        **{"cv_" + lang: ("cv.docx", "cv.pdf") for lang in ("ar", "en", "bilingual")},
        **{"minutes_" + lang: ("minutes.docx", "minutes.pdf") for lang in ("ar", "en")},
        **{
            "editing_" + mode: ("revision.txt", "changes.txt", "response.txt")
            for mode in ("proofread", "rewrite")
        },
        **{"word_pdf_" + mode: ("result.docx", "result.pdf") for mode in ("direct", "smart")},
        **{"translation_" + lang: ("translation.txt", "response.txt") for lang in ("ar", "en")},
    }
    if set(deliverables) != {case.name for case in result}:
        raise ValueError("Every acceptance case must declare its exact deliverables")
    result = representative_cases(
        [replace(case, expected_files=deliverables[case.name]) for case in result]
    )
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
