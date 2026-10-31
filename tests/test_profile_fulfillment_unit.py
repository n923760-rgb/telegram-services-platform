from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.publications import fulfillment as flow
from app.publications import prepared_page
from tests.profile_page_fixtures import plan, profile


@pytest.fixture(autouse=True)
def database():
    pass


def gateway():
    async def extract(schema, source, prompt):
        return schema.model_validate(plan())

    return SimpleNamespace(extract=AsyncMock(side_effect=extract))


@pytest.mark.parametrize("embedded", [True, False])
async def test_job_scoped_generation_preserves_native_snapshot_and_whole_page_target(embedded):
    ai, page = gateway(), uuid4()
    result = await flow.generate(
        ai,
        profile(),
        "هوية مستقلة لمصمم مع إبراز التواصل",
        publication_id=page,
        origin="https://profiles.example.invalid",
        embedded_qr=embedded,
    )
    assert ai.extract.await_count == 1 and result.kind == flow.KIND
    assert result.payload["profile"] == profile()
    assert result.payload["embedded_qr"] is embedded
    assert result.payload["public_url"] == f"https://profiles.example.invalid/p/{page.hex}"
    files = prepared_page.render(
        result.payload, publication_id=page, origin="https://profiles.example.invalid"
    )
    assert prepared_page.hashes(files) == result.payload["digests"]
    assert ai.extract.await_count == 1  # Native replay cannot spend again.


@pytest.mark.parametrize("change", ["origin", "identity", "source", "embedding"])
async def test_invalid_generation_input_rejects_before_provider_call(change):
    ai = gateway()
    args = dict(publication_id=uuid4(), origin="https://profiles.example.invalid", embedded_qr=True)
    source = profile()
    if change == "origin":
        args["origin"] += "/path"
    elif change == "identity":
        args["publication_id"] = "invalid"
    elif change == "source":
        source["name"] = ""
    else:
        args["embedded_qr"] = "yes"
    with pytest.raises(ValueError):
        await flow.generate(ai, source, "Customer brief", **args)
    ai.extract.assert_not_awaited()


async def test_invalid_ai_design_has_no_native_fallback():
    ai = SimpleNamespace(
        extract=AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda **kwargs: plan(action_order=[0, 0, 0]))
        )
    )
    with pytest.raises(ValueError):
        await flow.generate(
            ai,
            profile(),
            "Customer brief",
            publication_id=uuid4(),
            origin="https://profiles.example.invalid",
        )
    assert ai.extract.await_count == 1


def entitlement():
    return flow.HostingEntitlement(
        owner_id=1,
        order_id=uuid4(),
        publication_id=uuid4(),
        service_slug="fixture",
        service_version="7",
        payment_mode="test_credit",
        price_halala=100,
        price_stars=None,
        purchase_terms_hash=None,
        hosting_terms_hash="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner_id", True),
        ("expires_at", datetime.now()),
        ("hosting_terms_hash", "not a recorded policy hash"),
        ("unknown", "not a right"),
    ],
)
def test_right_is_strict_and_revalidates_mutated_instances(field, value):
    right = entitlement()
    with pytest.raises(ValidationError):
        flow.HostingEntitlement.model_validate({**right.model_dump(), field: value})
    if field != "unknown":
        changed = right.model_copy(update={field: value})
        with pytest.raises(ValidationError):
            flow.HostingEntitlement.model_validate(changed)


async def test_no_implicit_entitlement_resolver():
    from app.services.base import ServiceError

    with pytest.raises(ServiceError, match="not_allowed"):
        await flow.transfer(
            1, uuid4(), origin="https://profiles.example.invalid", resolve_entitlement=None
        )
