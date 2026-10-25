from io import BytesIO
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def table_pdf(language="en", *, pages=1, ruled=True, visual_arabic=False, form=False):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if "TableFixture" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("TableFixture", str(path)))
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(600, 800))
    rows = [["ID", "Amount", "Note"], ["00123", "125.50", "=1+1"], ["00017", "0", "2026-10-10"]]
    if language == "ar":
        rows[0] = ["رقم", "مبلغ", "بيان"]
        rows[1][2] = "مرحبا"
    if visual_arabic:
        import arabic_reshaper
        from bidi.algorithm import get_display

        rows = [[get_display(arabic_reshaper.reshape(cell)) for cell in row] for row in rows]
    for _ in range(pages):
        pdf.setFont("TableFixture", 12)
        for r, row in enumerate(rows):
            for c, text in enumerate(row):
                pdf.drawString(60 + c * 160, 715 - r * 40, text)
        if ruled:
            for x in [50, 210, 370, 530]:
                pdf.line(x, 620, x, 740)
            for y in [620, 660, 700, 740]:
                pdf.line(50, y, 530, y)
        if form:
            pdf.acroForm.textfield(
                name="account", value="00999", x=375, y=663, width=150, height=33
            )
        pdf.showPage()
    pdf.save()
    return output.getvalue(), rows
