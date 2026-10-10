import hashlib
import json
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core.db import sessions
from app.core.models import Job, Order, Service, StarCheckout, User
from app.core.transactions import transaction_retry
from app.orders.locking import lock_order
from app.orders.state import transition
from app.payments.billing import capture_order, refund_order, reserve_order
from app.services.base import InputSchema, Result, ServiceError
from app.services.registry import registry


@transaction_retry
async def register(user_id: int):
    if user_id <= 0:
        raise ServiceError("invalid_request")
    async with sessions.begin() as db:
        await db.execute(
            insert(User).values(id=user_id, language="ar", banned=False).on_conflict_do_nothing()
        )


@transaction_retry
async def submit(
    user_id: int,
    slug: str,
    inputs: dict,
    expected_price: int,
    key: str,
    expected_version: str | None = None,
    *,
    expected_stars: int | None = None,
    terms_version: str | None = None,
    expected_terms_hash: str | None = None,
):
    from app.core.settings import config

    mode = "stars" if expected_stars is not None else "test_credit"
    from app.payments.stars import terms_hash

    if config().stars_enabled != (mode == "stars"):
        raise ServiceError("payment_changed")
    if mode == "stars" and (
        type(expected_stars) is not int
        or not 1 <= expected_stars <= 1000000
        or terms_version != config().stars_terms_version
        or expected_terms_hash != terms_hash()
    ):
        raise ServiceError("payment_changed")
    if mode == "test_credit" and (terms_version is not None or expected_terms_hash is not None):
        raise ServiceError("payment_changed")
    digest = hashlib.sha256(
        json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    async with sessions.begin() as db:
        user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None or user.banned:
            raise ServiceError("not_allowed")
        previous = await db.scalar(
            select(Order).where(Order.user_id == user_id, Order.idempotency_key == key)
        )
        if previous:
            if (
                previous.service_slug != slug
                or (
                    previous.input_hash != digest
                    and not (previous.input_hash == "legacy" and previous.inputs == inputs)
                )
                or previous.price_halala != expected_price
                or previous.payment_mode != mode
                or previous.price_stars != expected_stars
                or previous.terms_version != terms_version
                or previous.terms_hash != expected_terms_hash
                or (expected_version is not None and previous.service_version != expected_version)
            ):
                raise ServiceError("invalid_request")
            return previous.id
        service = await db.scalar(select(Service).where(Service.slug == slug).with_for_update())
        if not service or not service.enabled or slug not in registry.types:
            raise ServiceError("unavailable")
        if mode == "test_credit" and service.price_halala != expected_price:
            raise ServiceError("price_changed")
        if mode == "stars" and service.price_stars != expected_stars:
            raise ServiceError("price_changed")
        if service.version != registry.types[slug].version or (
            expected_version is not None and expected_version != service.version
        ):
            raise ServiceError("service_changed")
        InputSchema.model_validate(service.input_schema).validate_inputs(inputs)
        from app.ops.costs import check_admission
        from app.ops.settings import setting

        await check_admission(db, user_id)
        if registry.types[slug].needs_ai(inputs):
            if not config().ai_enabled or await setting(db, "PROVIDER_PAUSED", default=False):
                raise ServiceError("provider_config")
        active = await db.scalar(
            select(func.count(Order.id)).where(
                Order.user_id == user_id,
                Order.status.in_(
                    [
                        "awaiting_payment",
                        "queued",
                        "processing",
                        "delivering",
                        "waiting_confirmation",
                    ]
                ),
            )
        )
        if active >= int(await setting(db, "MAX_CONCURRENT_JOBS_PER_USER")):
            raise ServiceError("concurrent_limit")
        order = Order(
            id=uuid4(),
            user_id=user_id,
            service_slug=slug,
            price_halala=expected_price,
            inputs=inputs,
            input_hash=digest,
            input_schema_snapshot=service.input_schema,
            service_version=service.version,
            idempotency_key=key,
            status="awaiting_payment" if mode == "stars" else "queued",
            payment_mode=mode,
            price_stars=expected_stars,
            terms_version=terms_version,
            terms_hash=expected_terms_hash,
            terms_snapshot={"ar": config().stars_terms_ar, "en": config().stars_terms_en}
            if mode == "stars"
            else None,
        )
        db.add(order)
        await db.flush()
        await reserve_order(db, order)
        if mode == "stars":
            from datetime import UTC, datetime, timedelta

            db.add(
                StarCheckout(
                    order_id=order.id, expires_at=datetime.now(UTC) + timedelta(minutes=15)
                )
            )
        else:
            db.add(Job(order_id=order.id, status="pending"))
        return order.id


async def fail_locked(db, order, key="service_failed", cancelled=False):
    if order.status in {"completed", "failed", "cancelled", "refunded"}:
        return
    await refund_order(db, order)
    transition(order, "cancelled" if cancelled else "failed")
    order.error_key = key
    job = await db.scalar(select(Job).where(Job.order_id == order.id))
    if job:
        job.status = "cancelled" if cancelled else "failed"
        job.lease_until = None
        from datetime import UTC, datetime

        job.finished_at = datetime.now(UTC)


async def complete_locked(db, order):
    await capture_order(db, order)
    transition(order, "completed")


@transaction_retry
async def confirm_structure(order_id, user_id, approved, *, expected_prepared=None):
    from datetime import UTC, datetime

    async with sessions.begin() as db:
        order = await lock_order(db, order_id)
        if not order or order.user_id != user_id:
            raise ServiceError("not_allowed")
        user = await db.get(User, user_id)
        if user.banned:
            raise ServiceError("not_allowed")
        if order.status != "waiting_confirmation":
            raise ServiceError("invalid_request")
        if (
            expected_prepared is not None
            and bool((order.result or {}).get("prepared_delivery")) != expected_prepared
        ):
            raise ServiceError("stale_button")
        if not approved:
            await fail_locked(db, order, "cancelled", cancelled=True)
            return
        result = order.result or {}
        if result.get("prepared_delivery"):
            prepared = Result.model_validate(result)
            prepared.prepared_delivery = False
            prepared.needs_confirmation = False
            prepared.continuation = {}
            order.result = prepared.model_dump(mode="json")
        else:
            order.inputs = {**order.inputs, "__continuation": result.get("continuation", {})}
            order.result = None
        order.confirmation_notified = False
        transition(order, "queued")
        job = await db.scalar(select(Job).where(Job.order_id == order.id).with_for_update())
        job.status = "pending"
        job.failure_count = 0
        job.next_run_at = datetime.now(UTC)
        job.lease_until = None
