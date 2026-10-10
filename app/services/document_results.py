"""Shared delivery preparation for builder-owned Word/PDF pairs."""

from app.providers.documents.base import DocumentError
from app.services.base import Result, ServiceError


async def word_pdf_result(
    runtime, document, *, preview, preview_localizations=None, include_title=True, filename="result"
):
    if runtime.renderer is None:
        raise ServiceError("document_render_unavailable")
    try:
        files = await runtime.renderer.word_pdf(document, include_title=include_title)
    except DocumentError as error:
        if error.key == "document_render_limit":
            raise ServiceError("input_invalid") from None
        raise ServiceError(error.key, transient=error.transient) from None
    artifacts = []
    try:
        artifacts.append(
            runtime.storage.save(
                filename + ".docx",
                files.docx,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        )
        artifacts.append(runtime.storage.save(filename + ".pdf", files.pdf, "application/pdf"))
    except BaseException:
        for artifact in artifacts:
            runtime.storage.delete(artifact.key)
        raise
    return Result(
        preview=preview, preview_localizations=preview_localizations or {}, artifacts=artifacts
    )
