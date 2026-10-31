"""Internal metered generation -> prepared handoff -> private draft projection.

No registered plugin, HTTP route, dispatcher or default hosting entitlement.
The mandatory DB-only resolver must read an explicitly confirmed purchase right;
returning this model is not a way to create or infer that right from payment alone.
"""

import asyncio
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid5

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Order, OrderCompletion, User
from app.orders import completions
from app.publications import design, prepared_page, repository
from app.services.base import ServiceError
from app.services.completion import Completion

KIND = "profile_page_v1"
REVISION_NAMESPACE = UUID("c9ece29b-785b-45e4-9e88-68a511077235")


class HostingEntitlement(BaseModel):
    """Trusted adapter result from persistent, owner-confirmed hosting rights.

    The production issuer/resolver and checkout evidence do not exist yet.
    Never construct this from customer/AI fields or a generic completed order.
    """

    model_config = ConfigDict(extra="forbid", strict=True, revalidate_instances="always")

    owner_id: StrictInt = Field(gt=0, lt=2**63)
    order_id: UUID
    publication_id: UUID
    service_slug: str = Field(min_length=1, max_length=64)
    service_version: str = Field(min_length=1, max_length=32)
    payment_mode: Literal["test_credit", "stars"]
    price_halala: StrictInt = Field(gt=0)
    price_stars: StrictInt | None
    purchase_terms_hash: str | None
    hosting_terms_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expires_at: AwareDatetime

    def matches(self, order, publication_id):
        return (
            (self.owner_id, self.order_id, self.publication_id)
            == (order.user_id, order.id, publication_id)
            and (
                self.service_slug,
                self.service_version,
                self.payment_mode,
                self.price_halala,
                self.price_stars,
                self.purchase_terms_hash,
            )
            == (
                order.service_slug,
                order.service_version,
                order.payment_mode,
                order.price_halala,
                order.price_stars,
                order.terms_hash,
            )
            and self.expires_at > datetime.now(UTC)
        )


async def generate(ai, profile, brief, *, publication_id, origin, embedded_qr=True):
    """Caller injects the original job-scoped metered gateway and trusted page ID."""
    publication_id = repository.uuid(publication_id)
    prepared_page.public_url(origin, publication_id)  # Reject destination before spending.
    if type(embedded_qr) is not bool:
        raise ValueError("explicit QR embedding choice required")
    source = design.Profile.model_validate(profile)
    plan = await design.compose(ai, source, brief)
    snapshot = await asyncio.to_thread(
        prepared_page.prepare,
        source,
        plan,
        publication_id=publication_id,
        origin=origin,
        embedded_qr=embedded_qr,
    )
    return Completion(kind=KIND, payload=snapshot)


async def transfer(owner_id, order_id, *, origin, resolve_entitlement):
    """Native verification before DB work; projection and handoff receipt commit once.

    resolve_entitlement(db, locked_order) is mandatory trusted DB-only code. It
    must validate/read durable reviewed rights and may allocate them in this same
    transaction. No default resolver, network call or independent commit is allowed.
    This function is internal, not owner authentication or commercial eligibility.
    """
    repository.identity(owner_id)
    order_id = repository.uuid(order_id)
    if not callable(resolve_entitlement):
        raise ServiceError("not_allowed")
    async with sessions() as db:
        order = await db.get(Order, order_id)
        user = await db.get(User, owner_id)
        row = await db.scalar(
            select(OrderCompletion).where(
                OrderCompletion.order_id == order_id,
                OrderCompletion.owner_id == owner_id,
                OrderCompletion.kind == KIND,
            )
        )
        if (
            not order
            or order.user_id != owner_id
            or order.status != "completed"
            or not user
            or user.banned
            or not row
        ):
            raise ServiceError("not_allowed")
        if row.state == "applied":

            async def unexpected(*args):
                raise ServiceError("invalid_request")

            # Recheck eligibility under locks; never recreate after stop/deletion.
            applied = True
        elif row.state != "pending" or row.expires_at <= datetime.now(UTC):
            raise ServiceError("unavailable")
        else:
            applied = False
            payload = Completion(kind=KIND, payload=row.payload).payload
            expected_hash = row.content_hash
    if applied:
        return await completions.consume(order_id, owner_id, KIND, unexpected)

    value = Completion(kind=KIND, payload=payload)
    if value.digest() != expected_hash:
        raise ServiceError("invalid_request")
    snapshot = prepared_page.Snapshot.model_validate(payload)
    publication_id = repository.uuid(snapshot.publication_id)
    # All four exact byte hashes are checked outside a DB transaction; no AI call.
    await prepared_page.render_async(payload, publication_id=publication_id, origin=origin)

    async def apply(db, order, actual):
        if Completion(kind=KIND, payload=actual).digest() != expected_hash:
            raise ServiceError("invalid_request")
        right = HostingEntitlement.model_validate(await resolve_entitlement(db, order))
        if not right.matches(order, publication_id):
            raise ServiceError("not_allowed")
        allocated = await repository.create_in_transaction(
            db,
            owner_id,
            order_id,
            expires_at=right.expires_at,
            publication_id=publication_id,
        )
        await repository.revise_in_transaction(
            db,
            owner_id,
            allocated,
            actual,
            expected_revision=0,
            operation_id=uuid5(REVISION_NAMESPACE, str(order_id)),
        )

    return await completions.consume(order_id, owner_id, KIND, apply)
