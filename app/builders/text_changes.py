"""Literal customer-owned text comparison; no AI, markup or inferred corrections."""

from app.core.i18n import tr


def build(source: str, revised: str, *, language: str) -> str:
    if not 1 <= len(source) <= 12000 or not 1 <= len(revised) <= 24000:
        raise ValueError("text comparison size limit")
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    revised = revised.replace("\r\n", "\n").replace("\r", "\n")
    before, after = source.split("\n"), revised.split("\n")
    changes = [
        (number, old, new)
        for number, (old, new) in enumerate(zip(before, after, strict=True), 1)
        if old != new
    ]
    parts = [
        tr("editing_changes_title", language),
        tr("editing_changes_summary", language, changed=len(changes), total=len(before)),
        tr("editing_changes_scope", language),
    ]
    if not changes:
        parts.append(tr("editing_changes_none", language))
    for number, old, new in changes:
        parts.extend(
            [
                "",
                tr("editing_changes_line", language, number=number),
                tr("editing_changes_before", language),
                old,
                tr("editing_changes_after", language),
                new,
            ]
        )
    # Full original context also makes unchanged records independently reviewable.
    parts.extend(["", tr("editing_changes_source", language), source])
    report = "\n".join(parts)
    if len(report) > 64000:
        raise ValueError("text comparison output limit")
    return report
