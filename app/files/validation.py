import logging
import warnings
import wave
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.base import ServiceError

Image.MAX_IMAGE_PIXELS = 20000000
ALLOWED_FILE_MIMES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "audio/ogg",
    "audio/mpeg",
    "audio/wav",
}


def image(data: bytes, max_bytes: int) -> bytes:
    if not data or len(data) > max_bytes:
        raise ServiceError("file_invalid")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as picture:
                if picture.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ServiceError("file_invalid")
                if picture.width < 32 or picture.height < 32:
                    raise ServiceError("image_unclear")
                picture.load()
                picture = ImageOps.exif_transpose(picture)
                picture = picture.convert("RGB")
                if (
                    max(picture.convert("L").getextrema()) - min(picture.convert("L").getextrema())
                    < 3
                ):
                    raise ServiceError("image_unclear")
                picture.thumbnail((1024, 1024))
                output = BytesIO()
                picture.save(output, format="JPEG", quality=88, optimize=True)
                return output.getvalue()
    except ServiceError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ServiceError("file_invalid") from None


def validate_file(data, mime, max_bytes):
    if not data or len(data) > max_bytes or mime not in ALLOWED_FILE_MIMES:
        raise ServiceError("file_invalid")
    if mime.startswith("image/"):
        return image(data, max_bytes)
    try:
        if mime == "application/pdf":
            from pypdf import PdfReader

            logging.getLogger("pypdf").setLevel(logging.CRITICAL)
            if not data.startswith(b"%PDF-"):
                raise ValueError
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise ValueError
            count = reader.trailer["/Root"]["/Pages"].get("/Count", 0)
            if (
                not isinstance(count, int)
                or not 1 <= count <= 200
                or not 1 <= len(reader.pages) <= 200
            ):
                raise ValueError
        elif mime == "audio/wav":
            with wave.open(BytesIO(data), "rb") as sound:
                expected = sound.getnframes() * sound.getnchannels() * sound.getsampwidth()
                if (
                    expected <= 0
                    or expected > max_bytes
                    or len(sound.readframes(sound.getnframes())) != expected
                ):
                    raise ValueError
        elif mime == "audio/ogg":
            if len(data) < 27 or data[:5] != b"OggS\x00":
                raise ValueError
            segments = data[26]
            header = 27 + segments
            if len(data) < header + sum(data[27:header]):
                raise ValueError
            if not data[header:].startswith((b"OpusHead", b"\x01vorbis")):
                raise ValueError
        elif mime == "audio/mpeg":
            offset = 0
            if data.startswith(b"ID3"):
                if len(data) < 10 or data[3] not in {2, 3, 4} or any(x >= 128 for x in data[6:10]):
                    raise ValueError
                offset = 10 + sum(
                    byte << shift for byte, shift in zip(data[6:10], (21, 14, 7, 0), strict=True)
                )
                if data[3] == 4 and data[5] & 16:
                    offset += 10
            frame = data[offset : offset + 4]
            if (
                len(frame) < 4
                or frame[0] != 255
                or frame[1] & 224 != 224
                or frame[1] & 24 == 8
                or frame[1] & 6 == 0
                or frame[2] >> 4 in {0, 15}
                or frame[2] & 12 == 12
            ):
                raise ValueError
    except Exception:
        raise ServiceError("file_invalid") from None
    return data
