from app.core.settings import config
from app.files.validation import validate_file
from app.providers.runtime import storage
from app.providers.telegram_files import TelegramFiles
from app.services.base import ServiceError


async def receive(message, kind, user_id):
    cfg = config()
    if kind == "image":
        if message.photo:
            media = message.photo[-1]
            mime = "image/jpeg"
        elif message.document and message.document.mime_type in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            media = message.document
            mime = media.mime_type
        else:
            raise ServiceError("file_invalid")
    elif kind == "audio":
        media = message.voice or message.audio
        mime = getattr(media, "mime_type", None) or "audio/ogg"
    else:
        media = message.document
        mime = getattr(media, "mime_type", None)
    if media is None or not media.file_size or media.file_size > cfg.max_file_bytes:
        raise ServiceError("file_invalid")
    try:
        # The storage factory may create its root directory; its I/O failure, the best-effort
        # quota pre-check below (authoritative check runs inside save() under the same lock),
        # and the download/save are all transient and map to the safe retry message below.
        store = storage()
        store.ensure_quota(user_id, media.file_size)
        content = await TelegramFiles(message.bot, cfg.max_file_bytes).download(media.file_id)
        content = validate_file(content, mime, cfg.max_file_bytes)
        if mime.startswith("image/"):
            mime = "image/jpeg"
        extension = {
            "application/pdf": "pdf",
            "audio/ogg": "ogg",
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
        }.get(mime, "jpg")
        return store.save(user_id, "input." + extension, content, mime).key
    except ServiceError:
        raise
    except Exception:
        # Telegram download and storage I/O failures are transient: surface a safe
        # localized retry message instead of leaking the transport error, and leave the
        # intake FSM state (and any reservation) untouched for a clean retry.
        raise ServiceError("input_retry", transient=True) from None
