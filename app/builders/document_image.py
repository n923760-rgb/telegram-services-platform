"""Conservative contrast enhancement of bounded document images, without text synthesis."""

from io import BytesIO

from PIL import Image

from app.files.validation import image_pixels

FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


def build(data: bytes, mode: str = "contrast"):
    if mode not in {"contrast", "grayscale", "sharpen"}:
        raise ValueError("unsupported mode")
    # Keep source pixels without the old intermediate JPEG encode; never upscale.
    original = image_pixels(data, 10 * 1024 * 1024, max_side=2048)
    with Image.open(BytesIO(data)) as source:
        extension, mime = FORMATS[source.format]
    import cv2
    import numpy as np

    pixels = np.array(original)
    if mode == "sharpen":
        # Bounded luminance-only edge contrast; no reconstruction or text synthesis.
        light = np.array(original.convert("L")).astype(np.float32)
        detail = light - cv2.GaussianBlur(light, (0, 0), sigmaX=1.0)
        delta = np.clip(0.8 * detail, -12, 12)
        processed = Image.fromarray(
            np.clip(pixels.astype(np.float32) + delta[:, :, None], 0, 255).astype(np.uint8)
        )
        return extension, mime, *_outputs(original, processed)
    lab = cv2.cvtColor(pixels, cv2.COLOR_RGB2LAB)
    light = lab[:, :, 0]
    residual = np.abs(light.astype(np.int16) - cv2.medianBlur(light, 3).astype(np.int16))
    # Only denoise detected high-frequency texture, blending to retain weak strokes.
    if np.median(residual) >= 2:
        filtered = cv2.bilateralFilter(light, 5, 18, 2)
        light = cv2.addWeighted(light, 0.5, filtered, 0.5, 0)
    # Estimate paper illumination after filling dark foreground strokes. Blurring
    # text directly would create bright halos around words/stamps during division.
    kernel_size = max(15, min(101, (min(light.shape) // 5) | 1))
    paper = cv2.morphologyEx(
        light,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size)),
    )
    background = cv2.GaussianBlur(
        paper.astype(np.float32), (0, 0), sigmaX=max(3, min(light.shape) / 20)
    )
    low, high = np.percentile(background, (10, 90))
    # Avoid treating dark pages/flat images as uneven white paper. No cropping,
    # thresholding, geometric correction, learned reconstruction or text synthesis.
    if np.median(light) > 110 and high - low > 18:
        gain = np.clip(high / np.maximum(background, 32), 1.0, 1.6)
        light = np.clip(light.astype(np.float32) * gain, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8, 8))
    adjusted = cv2.addWeighted(light, 0.65, clahe.apply(light), 0.35, 0)
    if mode == "grayscale":
        processed = Image.fromarray(adjusted).convert("RGB")
    else:
        lab[:, :, 0] = adjusted
        processed = Image.fromarray(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB))
    return extension, mime, *_outputs(original, processed)


def _outputs(original, processed):
    before, after = original.copy(), processed.copy()
    before.thumbnail((1024, 1024))
    after.thumbnail((1024, 1024))
    comparison = Image.new("RGB", (before.width * 2, before.height), "white")
    comparison.paste(before, (0, 0))
    comparison.paste(after, (before.width, 0))
    outputs = []
    for picture in (processed, comparison):
        stream = BytesIO()
        picture.save(stream, format="PNG")
        payload = stream.getvalue()
        if not payload or len(payload) > 10 * 1024 * 1024:
            raise ValueError("output limit")
        outputs.append(payload)
    return outputs
