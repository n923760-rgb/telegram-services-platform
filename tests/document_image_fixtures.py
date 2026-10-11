"""Synthetic document fixtures; never use customer images or identifiers here."""

from io import BytesIO

import numpy as np
from PIL import Image

from tests.ocr_fixtures import printed


def shaded(text="Invoice 00123\nTotal 125.50\nDate 2026-10-09"):
    with Image.open(BytesIO(printed(text))) as source:
        pixels = np.array(source).astype(np.float32)
    height, width = pixels.shape[:2]
    gradient = np.linspace(0.58, 1.0, width)[None, :, None]
    texture = (3 * np.sin(np.arange(height) * 2.0))[:, None, None]
    pixels = np.clip(pixels * gradient + texture, 0, 255).astype(np.uint8)
    # A colored stamp outside text: luminance adjustment must not erase color.
    pixels[225:265, 820:940] = (40, 90, 180)
    output = BytesIO()
    Image.fromarray(pixels).save(output, "PNG")
    return output.getvalue()


def check_quality(enhanced):
    source = np.array(Image.open(BytesIO(shaded())).convert("L"))
    image = Image.open(BytesIO(enhanced)).convert("RGB")
    output = np.array(image.convert("L"))
    # Blank-paper strip has no text/stamp; measure illumination variation there.
    assert np.std(output[280:295, 30:970]) < np.std(source[280:295, 30:970]) * 0.6
    color = np.array(image)[240, 880].astype(int)
    assert color[2] > color[1] + 40 and color[1] > color[0] + 20
