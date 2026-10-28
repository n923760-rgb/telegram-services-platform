"""Bounds before persistence; content stays data rather than trusted markup."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.publications import repository as pages


@pytest.fixture(autouse=True)
def database():
    pass


def test_canonical_content_hash_preserves_exact_text_and_targets():
    a = {"name": "محمد", "url": "https://example.invalid/?id=00123"}
    result, digest = pages.content_snapshot(a)
    assert result == a and result is not a
    assert digest == pages.content_snapshot(dict(reversed(list(a.items()))))[1]
    assert digest != pages.content_snapshot({**a, "name": "محمد "})[1]
    result["name"] = "edited"
    assert a["name"] == "محمد"


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {},
        {1: "x"},
        {"v": float("nan")},
        {"v": b"x"},
        {"v": 1.2},
        {"v": "\ud800"},
        {"v": "ع" * 20000},
    ],
)
def test_invalid_or_oversized_content_rejected(value):
    with pytest.raises(pages.PublicationError, match="invalid_content"):
        pages.content_snapshot(value)


def test_excessive_depth_rejected():
    value = {"v": "x"}
    for _ in range(10):
        value = {"v": value}
    with pytest.raises(pages.PublicationError):
        pages.content_snapshot(value)


@pytest.mark.parametrize("owner", [True, "1", None, 0, -1, 2**63])
async def test_invalid_identity_cannot_reach_database(owner):
    with pytest.raises(pages.PublicationError, match="unavailable"):
        await pages.create(owner, uuid4(), expires_at=datetime.now())


async def test_naive_hosting_expiry_rejected_before_database():
    with pytest.raises(pages.PublicationError, match="invalid_input"):
        await pages.create(1, uuid4(), expires_at=datetime.now())


@pytest.mark.parametrize("revision", [True, -1, 21, "1", None])
async def test_invalid_revision_rejected_before_database(revision):
    with pytest.raises(pages.PublicationError):
        await pages.revise(
            1, uuid4(), {"name": "x"}, expected_revision=revision, operation_id=uuid4()
        )


async def test_malformed_public_identifier_returns_no_content():
    assert await pages.public_content("wrong") is None
