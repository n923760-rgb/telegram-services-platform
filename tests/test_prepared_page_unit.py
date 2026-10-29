"""Prepared bytes, stable destinations and fail-closed renderer drift without DB/AI."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.builders import publication_page
from app.publications import prepared_page as prepared
from app.publications.repository import content_snapshot
from tests.profile_page_fixtures import plan, profile

ORIGIN = "https://profiles.example.invalid"


@pytest.fixture(autouse=True)
def database():
    pass


def fixture(*, embedded_qr=True):
    identity = uuid4()
    snapshot = prepared.prepare(
        profile(), plan(), publication_id=identity, origin=ORIGIN, embedded_qr=embedded_qr
    )
    return identity, snapshot


@pytest.mark.parametrize("embedded", [True, False])
def test_durable_json_roundtrip_preserves_exact_bundle_and_derived_url(embedded):
    identity, snapshot = fixture(embedded_qr=embedded)
    durable, digest = content_snapshot(snapshot)
    files = prepared.render(durable, publication_id=identity, origin=ORIGIN)
    url = f"{ORIGIN}/p/{identity.hex}"
    assert snapshot["public_url"] == url and len(digest) == 64
    assert files == publication_page.bundle(profile(), plan(), public_url=url, embedded_qr=embedded)
    assert prepared.hashes(files) == durable["digests"]
    assert (b"<details" in files["profile.html"]) is embedded


@pytest.mark.parametrize(
    "origin",
    [
        "http://example.invalid",
        "https://example.invalid/path",
        "https://user:pass@example.invalid",
        "https://example.invalid?x=1",
        "https://example.invalid#fragment",
        "https://example.invalid?",
        "https://example.invalid#",
        "https://example.invalid/\n",
        "javascript:1",
        None,
    ],
)
def test_destination_requires_a_trusted_https_origin_not_an_arbitrary_path(origin):
    with pytest.raises(prepared.PreparedPageError):
        prepared.public_url(origin, uuid4())


def test_origin_trailing_slash_and_uuid_text_derive_one_stable_destination():
    identity = uuid4()
    assert prepared.public_url(ORIGIN, identity) == prepared.public_url(ORIGIN + "/", str(identity))


@pytest.mark.parametrize(
    "change", ["id", "origin", "url", "source", "plan", "digest", "missing", "extra"]
)
def test_snapshot_cannot_move_to_other_page_origin_or_different_content(change):
    identity, content = fixture()
    snapshot = deepcopy(content)
    origin = ORIGIN
    if change == "id":
        identity = uuid4()
    elif change == "origin":
        origin = "https://other.example.invalid"
    elif change == "url":
        snapshot["public_url"] = "https://attacker.example.invalid"
    elif change == "source":
        snapshot["profile"]["actions"][0]["url"] = "https://attacker.example.invalid"
    elif change == "plan":
        snapshot["plan"]["corner_radius"] = 0
    elif change == "digest":
        snapshot["digests"]["profile.html"] = "a" * 64
    elif change == "missing":
        del snapshot["digests"]["qr.svg"]
    else:
        snapshot["html"] = "<script>untrusted</script>"
    with pytest.raises(prepared.PreparedPageError, match="unavailable"):
        prepared.render(snapshot, publication_id=identity, origin=origin)


@pytest.mark.parametrize("filename", sorted(prepared.FILES))
def test_any_export_drift_blocks_reuse_instead_of_silently_changing_consent(filename, monkeypatch):
    identity, snapshot = fixture()
    original = publication_page.bundle

    def changed(*args, **kwargs):
        files = original(*args, **kwargs)
        files[filename] += b"changed renderer or font"
        return files

    monkeypatch.setattr(publication_page, "bundle", changed)
    with pytest.raises(prepared.PreparedPageError, match="unavailable"):
        prepared.render(snapshot, publication_id=identity, origin=ORIGIN)


async def test_public_adapter_hides_missing_and_drifted_content(monkeypatch):
    identity, snapshot = fixture()

    async def content(_):
        return snapshot

    monkeypatch.setattr(prepared.repository, "public_content", content)
    assert set(await prepared.public_bundle(identity, origin=ORIGIN)) == prepared.FILES
    assert await prepared.public_bundle(uuid4(), origin=ORIGIN) is None
    snapshot["digests"]["profile.html"] = "b" * 64
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None
    snapshot = None
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None


@pytest.mark.parametrize("digest", ["", "a" * 63, "G" * 64, True, 42, "a" * 64 + "\n"])
async def test_invalid_review_hash_is_rejected_before_db(digest):
    with pytest.raises(prepared.repository.PublicationError, match="invalid_input"):
        await prepared.repository.publish(
            1,
            uuid4(),
            revision=1,
            expected_active=None,
            expected_expires_at=datetime.now(UTC),
            terms_hash="d" * 64,
            expected_content_hash=digest,
            operation_id=uuid4(),
        )


async def test_approve_rechecks_review_before_calling_db_consent(monkeypatch):
    identity, snapshot = fixture()
    calls = []

    async def review(*args, **kwargs):
        return {"revision": 2, "active_revision": 1, "content_hash": "c" * 64}

    async def publish(*args, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(prepared, "review", review)
    monkeypatch.setattr(prepared.repository, "publish", publish)
    with pytest.raises(prepared.repository.PublicationError, match="revision_changed"):
        await prepared.approve(
            1,
            identity,
            origin=ORIGIN,
            revision=1,
            expected_active=None,
            expected_expires_at=datetime.now(UTC),
            content_hash="c" * 64,
            terms_hash="d" * 64,
            operation_id=uuid4(),
        )
    assert calls == []
    await prepared.approve(
        1,
        identity,
        origin=ORIGIN,
        revision=2,
        expected_active=1,
        expected_expires_at=datetime.now(UTC),
        content_hash="c" * 64,
        terms_hash="d" * 64,
        operation_id=uuid4(),
    )
    assert calls[0]["expected_content_hash"] == "c" * 64


@pytest.mark.parametrize("expiry", [None, "2026-12-01", True, datetime(2026, 12, 1)])
async def test_prepared_approval_cannot_skip_reviewed_hosting_expiry(expiry):
    with pytest.raises(prepared.repository.PublicationError, match="invalid_input"):
        await prepared.approve(
            1,
            uuid4(),
            origin=ORIGIN,
            revision=1,
            expected_active=None,
            expected_expires_at=expiry,
            content_hash="c" * 64,
            terms_hash="d" * 64,
            operation_id=uuid4(),
        )
