"""Customer comparison text stays separate from the clean edited deliverable."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.builders.text_changes import build
from app.core.i18n import tr
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_editing.schema import Inputs, revision_schema
from app.services.text_editing.service import TextEditing


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en"])
def test_only_changed_sections_have_exact_before_after_and_physical_line_refs(language):
    before = "الطلب 00123" if language == "ar" else "order 00123"
    after = "رقم الطلب 00123" if language == "ar" else "Order 00123"
    source = f"unchanged@example.invalid\n\n{before}\n0.00\n"
    revised = source.replace(before, after)
    report = build(source, revised, language=language)
    changes, original = report.split(tr("editing_changes_source", language) + "\n", 1)
    assert original == source
    assert tr("editing_changes_summary", language, changed=1, total=5) in changes
    assert tr("editing_changes_line", language, number=3) in changes
    assert f"{tr('editing_changes_before', language)}\n{before}" in changes
    assert f"{tr('editing_changes_after', language)}\n{after}" in changes
    assert "unchanged@example.invalid" not in changes and "0.00" not in changes


@pytest.mark.parametrize("language", ["ar", "en"])
def test_no_change_report_normalizes_line_endings_without_inventing_edits(language):
    source = "00123\r\n\r\nNo changes\r\n"
    normalized = source.replace("\r\n", "\n")
    report = build(source, normalized, language=language)
    assert tr("editing_changes_none", language) in report
    assert tr("editing_changes_summary", language, changed=0, total=4) in report
    assert report.endswith(normalized)
    assert tr("editing_changes_before", language) not in report


def test_whitespace_only_edits_are_visible_and_complete_long_lines_are_not_truncated():
    source = " a@example.invalid 00123 "
    revised = "a@example.invalid 00123"
    assert source in build(source, revised, language="en")
    source = ("أ" * 149 + "\n") * 80
    revised = ("ب" * 299 + "\n") * 80
    report = build(source, revised, language="ar")
    changes, original = report.split(tr("editing_changes_source", "ar") + "\n", 1)
    assert original == source
    assert len(report) <= 64000
    assert changes.count("أ" * 149) == changes.count("ب" * 299) == 80


@pytest.mark.parametrize(
    "source,revised",
    [
        ("", "a"),
        ("a", ""),
        ("a" * 12001, "a"),
        ("a", "a" * 24001),
        ("a\n\nb", "a\nb"),
        ("a", "a\nb"),
    ],
)
def test_comparison_rejects_overflow_or_lost_line_alignment(source, revised):
    with pytest.raises(ValueError):
        build(source, revised, language="en")


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_service_adds_comparison_without_extra_ai_or_changing_final_text(tmp_path, language):
    source = "طلب 00123" if language == "ar" else "order 00123"
    revised = "الطلب 00123" if language == "ar" else "Order 00123"
    values = Inputs.parse({"text": source, "mode": "proofread"})
    schema = revision_schema(values)
    ai = AsyncMock(return_value=schema.model_validate({"segments": [{"id": 1, "text": revised}]}))
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    service = TextEditing()
    service.runtime = SimpleNamespace(storage=storage, ai=SimpleNamespace(extract=ai))
    result = await service.run({"text": source, "mode": "proofread"})
    assert result.text == revised and not result.needs_confirmation
    assert [a.filename for a in result.artifacts] == ["revision.txt", "changes.txt"]
    assert storage.read(result.artifacts[0].key).decode("utf-8") == revised
    assert storage.read(result.artifacts[1].key).decode("utf-8") == build(
        source, revised, language=language
    )
    assert ai.await_count == 1


@pytest.mark.parametrize("delete_failure", [False, True])
async def test_second_file_failure_keeps_original_error_and_cleans_partial_output(
    tmp_path, monkeypatch, delete_failure
):
    backend = LocalStorage(tmp_path)
    owned = OwnedStorage(backend, 7)
    original = owned.save
    values = Inputs.parse({"text": "order 00123", "mode": "proofread"})
    response = revision_schema(values).model_validate(
        {"segments": [{"id": 1, "text": "Order 00123"}]}
    )
    ai = AsyncMock(return_value=response)

    def save(name, *args):
        if name == "changes.txt":
            raise ServiceError("storage_quota")
        return original(name, *args)

    def unavailable(*args):
        raise OSError("synthetic delete failure")

    monkeypatch.setattr(owned, "save", save)
    if delete_failure:
        monkeypatch.setattr(owned, "delete", unavailable)
    service = TextEditing()
    service.runtime = SimpleNamespace(storage=owned, ai=SimpleNamespace(extract=ai))
    with pytest.raises(ServiceError, match="storage_quota"):
        await service.run({"text": values.text, "mode": "proofread"})
    assert ai.await_count == 1
    assert backend.usage(7)[1] == int(delete_failure)
    backend.expire_before(datetime.now(UTC) + timedelta(seconds=1))
    assert backend.usage(7) == (0, 0)
