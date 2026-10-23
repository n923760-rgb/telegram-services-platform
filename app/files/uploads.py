"""Validated, owner-bound received bytes shared by both customer adapters."""

from io import BytesIO

from PIL import Image

from app.core.settings import config
from app.files.validation import ALLOWED_FILE_MIMES, validate_file
from app.providers.runtime import storage
from app.services.base import ServiceError


def save_upload(user_id, content, mime, kind, *, preserve_image=False, store=None):
    images = {"image/jpeg", "image/png", "image/webp"}
    audio = {"audio/ogg", "audio/mpeg", "audio/wav"}
    allowed = images if kind == "image" else audio if kind == "audio" else ALLOWED_FILE_MIMES
    if kind not in {"image", "file", "audio"} or mime not in allowed:
        raise ServiceError("file_invalid")
    normalized = validate_file(content, mime, config().max_file_bytes)
    if mime in images:
        if preserve_image:
            with Image.open(BytesIO(content)) as picture:
                mime = Image.MIME[picture.format]
        else:
            content, mime = normalized, "image/jpeg"
    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
        "audio/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/wav": "wav",
    }[mime]
    return (store or storage()).save(user_id, "input." + extension, content, mime).key
