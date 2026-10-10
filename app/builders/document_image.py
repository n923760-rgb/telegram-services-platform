"""Conservative contrast enhancement of bounded document images, without text synthesis."""

from io import BytesIO

from PIL import Image

from app.files.validation import image

FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def build(data: bytes, mode: str):
    if mode not in {"contrast", "grayscale"}:
        raise ValueError("unsupported mode")
    # The shared validator bounds decoding and corrects EXIF. Processing is <=1024x1024.
    normalized = image(data, 10 * 1024 * 1024)
    with Image.open(BytesIO(data)) as source:
        extension, mime = FORMATS[source.format]
    with Image.open(BytesIO(normalized)) as source:
        original = source.convert("RGB")
    import cv2
    import numpy as np

    pixels = np.array(original)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    if mode == "grayscale":
        processed = Image.fromarray(clahe.apply(cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY))).convert(
            "RGB"
        )
    else:
        lab = cv2.cvtColor(pixels, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        processed = Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))
    comparison = Image.new("RGB", (original.width * 2, original.height), "white")
    comparison.paste(original, (0, 0))
    comparison.paste(processed, (original.width, 0))
    outputs = []
    for picture in (processed, comparison):
        stream = BytesIO()
        picture.save(stream, format="PNG")
        payload = stream.getvalue()
        if not payload or len(payload) > 10 * 1024 * 1024:
            raise ValueError("output limit")
        outputs.append(payload)
    return extension, mime, *outputs
