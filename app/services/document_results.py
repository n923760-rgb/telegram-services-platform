"""Shared delivery preparation for builder-owned Word/PDF pairs."""

from app.core.i18n import translations
from app.providers.documents.base import DocumentError
from app.services.base import Result, ServiceError


async def word_pdf_result(
    runtime, document, *, preview, preview_localizations=None, include_title=True, filename="result"
):
    if runtime.renderer is None:
        raise ServiceError("document_render_unavailable")
    try:
        files = await runtime.renderer.word_pdf(document, include_title=include_title)
        visual = (
            await runtime.previews.first_page(files.pdf)
            if getattr(runtime, "previews", None) is not None
            else None
        )
    except DocumentError as error:
        if error.key == "document_render_limit":
            raise ServiceError("input_invalid") from None
        raise ServiceError(error.key, transient=error.transient) from None
    artifacts = []
    images = []
    try:
        artifacts.append(
            runtime.storage.save(
                filename + ".docx",
                files.docx,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        )
        artifacts.append(runtime.storage.save(filename + ".pdf", files.pdf, "application/pdf"))
        if visual is not None:
            images.append(runtime.storage.save("preview.png", visual.png, "image/png"))
    except BaseException:
        for artifact in artifacts + images:
            runtime.storage.delete(artifact.key)
        raise
    if visual is not None:
        reviews = translations("document_visual_review", pages=visual.pages)
        return Result(
            preview=reviews["ar"],
            preview_localizations=reviews,
            artifacts=artifacts,
            preview_artifacts=images,
            prepared_delivery=True,
            needs_confirmation=True,
            continuation={"prepared": True},
        )
    return Result(
        preview=preview, preview_localizations=preview_localizations or {}, artifacts=artifacts
    )
