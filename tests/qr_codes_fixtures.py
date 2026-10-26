"""Synthetic QR payloads and independent native read-back; no test-runner dependency."""

import cv2
import numpy as np
import pypdfium2 as pdfium

from app.builders.qr_codes import CENTERS, PAGE_HEIGHT, QR_SIZE, TOPS


def inputs(**changes):
    return {"language": "en", "entries": "Website|https://example.invalid/?id=00123", **changes}


def decode_all(content, count):
    document = pdfium.PdfDocument(content)
    result = []
    try:
        for index in range(count):
            page = document[index // 6]
            bitmap = page.render(scale=3)
            try:
                image = np.array(bitmap.to_pil().convert("RGB"))
            finally:
                bitmap.close()
                page.close()
            offset = index % 6
            center, top = CENTERS[offset % 2], TOPS[offset // 2]
            x, y = round((center - QR_SIZE / 2 - 8) * 3), round((PAGE_HEIGHT - top - 8) * 3)
            crop = image[y : y + (QR_SIZE + 16) * 3, x : x + (QR_SIZE + 16) * 3]
            decoded, points, _ = cv2.QRCodeDetectorAruco().detectAndDecode(crop)
            assert points is not None, index
            result.append(decoded)
    finally:
        document.close()
    return result
