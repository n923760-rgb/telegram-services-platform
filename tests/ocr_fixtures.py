import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.providers.documents.tesseract import TesseractDocuments


def printed(text="Invoice 00123\nTotal 125.50\nDate 2026-10-09"):
    picture = Image.new("RGB", (1000, 300), "white")
    draw = ImageDraw.Draw(picture)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
    for index, line in enumerate(text.splitlines()):
        draw.text((40, 30 + index * 75), line, fill="black", font=font)
    output = BytesIO()
    picture.save(output, "PNG")
    return output.getvalue()


def processor():
    # Test-only local data override; production uses the distribution's packages.
    directory = os.getenv("LOCAL_OCR_TEST_TESSDATA")
    return TesseractDocuments(tessdata_dir=Path(directory) if directory else None)
