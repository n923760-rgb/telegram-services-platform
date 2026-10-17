"""Shared delivery preparation for builder-owned Word/PDF pairs."""

from app.core.i18n import translations
from app.providers.documents.base import DocumentError
from app.services.base import Result, ServiceError


async def word_pdf_result(
    runtime,
    document,
    *,
    preview,
    preview_localizations=None,
    include_title=True,
    filename="result",
    output_format=None,
):
    if output_format is not None and (
        not isinstance(output_format, str) or output_format not in {"word", "pdf", "both"}
    ):
        raise ServiceError("input_invalid")
    selected = output_format or "both"
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
        if selected in {"word", "both"}:
            artifacts.append(
                runtime.storage.save(
                    filename + ".docx",
                    files.docx,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            )
        if selected in {"pdf", "both"}:
            artifacts.append(runtime.storage.save(filename + ".pdf", files.pdf, "application/pdf"))
        if visual is not None:
            images.append(runtime.storage.save("preview.png", visual.png, "image/png"))
    except BaseException:
        for artifact in artifacts + images:
            runtime.storage.delete(artifact.key)
        raise
    reviews = (
        translations("document_visual_review", pages=visual.pages)
        if visual is not None
        else preview_localizations or {}
    )
    if output_format is not None:
        labels = translations("document_output_" + selected)
        reviews = {
            lang: translations("document_output_summary", format=labels[lang])[lang]
            + "\n\n"
            + reviews.get(lang, preview)
            for lang in ("ar", "en")
        }
        preview = reviews["ar"]
    if visual is not None:
        return Result(
            preview=reviews["ar"],
            preview_localizations=reviews,
            artifacts=artifacts,
            preview_artifacts=images,
            prepared_delivery=True,
            needs_confirmation=True,
            continuation={"prepared": True},
        )
    return Result(preview=preview, preview_localizations=reviews, artifacts=artifacts)
