"""Bounded image pages, with lossless decoded pixels and no source metadata."""

import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.builders.quality import validate

MAX_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 20_000_000
MARGIN = 28.35  # 10 mm


def build(images: list[bytes], *, orientation: str = "auto") -> bytes:
    if orientation not in {"auto", "portrait", "landscape"} or not 1 <= len(images) <= 5:
        raise ValueError("invalid image PDF request")
    if (
        any(not data or len(data) > MAX_BYTES for data in images)
        or sum(map(len, images)) > MAX_TOTAL_BYTES
    ):
        raise ValueError("image input limit")
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    pdf.setTitle("Images")
    pdf.setAuthor("")
    pixels = 0
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            for data in images:
                with Image.open(BytesIO(data)) as original:
                    if (
                        original.format not in {"JPEG", "PNG", "WEBP"}
                        or getattr(original, "n_frames", 1) != 1
                    ):
                        raise ValueError("unsupported image")
                    width, height = original.size
                    pixels += width * height
                    if min(width, height) < 32 or max(width, height) > 10000 or pixels > MAX_PIXELS:
                        raise ValueError("decoded image limit")
                    original.load()
                    with ImageOps.exif_transpose(original) as picture:
                        with picture.convert("RGBA") as rgba:
                            with Image.new("RGB", rgba.size, "white") as rgb:
                                with rgba.getchannel("A") as alpha:
                                    rgb.paste(rgba, mask=alpha)
                                use_landscape = orientation == "landscape" or (
                                    orientation == "auto" and rgb.width > rgb.height
                                )
                                page = landscape(A4) if use_landscape else A4
                                pdf.setPageSize(page)
                                ratio = min(
                                    (page[0] - 2 * MARGIN) / rgb.width,
                                    (page[1] - 2 * MARGIN) / rgb.height,
                                )
                                width, height = rgb.width * ratio, rgb.height * ratio
                                pdf.drawImage(
                                    ImageReader(rgb),
                                    (page[0] - width) / 2,
                                    (page[1] - height) / 2,
                                    width=width,
                                    height=height,
                                )
                                pdf.showPage()
        pdf.save()
        if output.tell() > MAX_BYTES:
            raise ValueError("image PDF output limit")
        return validate(output.getvalue(), "pdf")
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError("invalid image") from None
