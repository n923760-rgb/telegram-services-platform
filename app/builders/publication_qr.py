"""Native whole-page QR assets. The supplied destination is never chosen by AI."""

from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw
from reportlab.graphics.barcode.qr import QrCodeWidget

from app.publications.design import https_url

QUIET_ZONE = 4
PIXELS_PER_MODULE = 12


def matrix(url):
    https_url(url)
    widget = QrCodeWidget(url, barLevel="M", barBorder=QUIET_ZONE)
    widget.qr.make()
    return widget.qr.modules


def assets(url):
    modules = matrix(url)
    side = len(modules) + QUIET_ZONE * 2
    image = Image.new("RGB", (side, side), "white")
    draw = ImageDraw.Draw(image)
    boxes = []
    for y, row in enumerate(modules):
        for x, dark in enumerate(row):
            if dark:
                left, top = x + QUIET_ZONE, y + QUIET_ZONE
                draw.point((left, top), fill="black")
                boxes.append(f'<rect x="{left}" y="{top}" width="1" height="1"/>')
    image = image.resize((side * PIXELS_PER_MODULE,) * 2, Image.Resampling.NEAREST)
    output = BytesIO()
    image.save(output, format="PNG")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'width="{side * PIXELS_PER_MODULE}" height="{side * PIXELS_PER_MODULE}" '
        'role="img" aria-labelledby="qr-title" shape-rendering="crispEdges">'
        f'<title id="qr-title">{escape(url)}</title><rect width="100%" height="100%" fill="white"/>'
        f'<g fill="black">{"".join(boxes)}</g></svg>'
    )
    return {"qr.png": output.getvalue(), "qr.svg": svg.encode()}
