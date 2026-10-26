"""Vector QR sheets with four-module quiet zones and literal UTF-8 payloads."""

from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.builders.interactive_card import visual, wrapped
from app.builders.pdf import _register_fonts
from app.builders.quality import validate
from app.core.i18n import tr

PAGE_WIDTH, PAGE_HEIGHT = A4
QR_SIZE = 150
CENTERS = (PAGE_WIDTH / 4, PAGE_WIDTH * 3 / 4)
TOPS = (PAGE_HEIGHT - 80, PAGE_HEIGHT - 325, PAGE_HEIGHT - 570)


def build(values):
    _register_fonts()
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    pdf.setTitle(tr("qr_name", values.language))
    rows = values.rows()
    for start in range(0, len(rows), 6):
        pdf.setFillColor(HexColor("#0f172a"))
        pdf.setFont("DejaVu-Bold", 18)
        pdf.drawCentredString(
            PAGE_WIDTH / 2, PAGE_HEIGHT - 36, visual(tr("qr_name", values.language))
        )
        for offset, (label, payload) in enumerate(rows[start : start + 6]):
            center, top = CENTERS[offset % 2], TOPS[offset // 2]
            widget = QrCodeWidget(
                payload, barLevel="M", barBorder=4, barWidth=QR_SIZE, barHeight=QR_SIZE
            )
            # Widget uses the same ReportLab canvas through a vector drawing.
            drawing = Drawing(QR_SIZE, QR_SIZE)
            drawing.add(widget)
            renderPDF.draw(drawing, pdf, center - QR_SIZE / 2, top - QR_SIZE)
            pdf.setFillColor(black)
            pdf.setFont("DejaVu", 10)
            lines = wrapped(f"{start + offset + 1}. {label}", "DejaVu", 10, 220)
            if len(lines) > 2:
                raise ValueError("QR label exceeds layout")
            for index, line in enumerate(lines):
                pdf.drawCentredString(center, top - QR_SIZE - 18 - index * 14, visual(line))
        pdf.setFont("DejaVu", 8)
        pdf.drawCentredString(PAGE_WIDTH / 2, 24, f"{start // 6 + 1} / {(len(rows) + 5) // 6}")
        pdf.showPage()
    pdf.save()
    return validate(output.getvalue(), "pdf")
