from dataclasses import dataclass

from app.core.settings import config
from app.providers.ai.gateway import AI
from app.providers.ai.openai_compatible import OpenAICompatible
from app.providers.storage import LocalStorage, OwnedStorage


@dataclass
class Runtime:
    ai: AI | None
    storage: OwnedStorage


def provider():
    if config().ai_provider != "openai_compatible":
        raise ValueError("unsupported configured provider")
    return OpenAICompatible()


def storage():
    cfg = config()
    return LocalStorage(
        cfg.storage_root,
        cfg.max_file_bytes,
        quota_bytes=cfg.storage_quota_bytes,
        quota_files=cfg.storage_quota_files,
    )


def runtime_for(job_id, user_id, *, needs_ai=True):
    return Runtime(
        AI(provider(), job_id, user_id) if needs_ai else None, OwnedStorage(storage(), user_id)
    )
