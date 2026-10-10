from dataclasses import dataclass

from app.core.settings import config
from app.providers.ai.gateway import AI
from app.providers.ai.openai_compatible import OpenAICompatible
from app.providers.documents.base import DocumentProcessor
from app.providers.documents.libreoffice import LibreOfficeDocuments
from app.providers.documents.previews import PdfPreviews, PreviewRenderer
from app.providers.documents.rendering import DocumentRenderer
from app.providers.documents.tesseract import TesseractDocuments
from app.providers.storage import LocalStorage, OwnedStorage
from app.providers.tables.base import TableExtractor
from app.providers.tables.camelot import CamelotTables


@dataclass
class Runtime:
    ai: AI | None
    storage: OwnedStorage
    documents: DocumentProcessor | None = None
    renderer: DocumentRenderer | None = None
    tables: TableExtractor | None = None
    previews: PreviewRenderer | None = None


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
        AI(provider(), job_id, user_id) if needs_ai else None,
        OwnedStorage(storage(), user_id),
        TesseractDocuments(),
        LibreOfficeDocuments(),
        CamelotTables(),
        PdfPreviews() if config().document_visual_review else None,
    )
