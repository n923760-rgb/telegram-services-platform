"""Confirmed owner controls; snapshot intent and bounded DB-only recovery."""

import hashlib
import json
import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, text

from app.core.db import sessions
from app.core.models import (
    Order,
    Service,
    ServiceActivationChange,
    ServiceActivationTask,
    Setting,
    StarCharge,
)
from app.core.settings import config
from app.core.transactions import transaction_retry
from app.ops.readiness import ai_configuration
from app.orders.engine import fail_locked
from app.orders.locking import lock_order
from app.services.base import ServiceError
from app.services.registry import registry

ACTIVE = ("awaiting_payment", "queued", "processing", "waiting_confirmation", "delivering")
MAX_ORDERS = 100
MAX_CHARGES = 500


def authorize(actor_id):
    if type(actor_id) is not int or actor_id not in config().admin_ids:
        raise ServiceError("not_allowed")


def digest(snapshot):
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def snapshot(db, service):
    plugin = registry.types.get(service.slug)
    if plugin is None or not registry.customer_visible(service.slug):
        raise ServiceError("unavailable")
    rows = (
        await db.execute(
            select(
                Order.id, Order.status, Order.payment_mode, Order.price_halala, Order.price_stars
            )
            .where(Order.service_slug == service.slug, Order.status.in_(ACTIVE))
            .order_by(Order.id)
            .limit(MAX_ORDERS + 1)
        )
    ).all()
    if len(rows) > MAX_ORDERS:
        raise ServiceError("admin_activation_limit")
    charges = (
        await db.scalars(
            select(StarCharge)
            .join(Order, Order.id == StarCharge.order_id)
            .where(
                StarCharge.order_id.in_([row.id for row in rows]),
                StarCharge.user_id == Order.user_id,
            )
            .order_by(StarCharge.charge_id)
            .limit(MAX_CHARGES + 1)
        )
    ).all()
    if len(charges) > MAX_CHARGES:
        raise ServiceError("admin_activation_limit")
    return {
        "service": {
            "enabled": service.enabled,
            "version": service.version,
            "price_halala": service.price_halala,
            "price_stars": service.price_stars,
        },
        "source_version": plugin.version,
        "stars_enabled": config().stars_enabled,
        "ai_state": await ai_configuration(db),
        "orders": [
            {
                "id": str(row.id),
                "status": row.status,
                "mode": row.payment_mode,
                "halalas": row.price_halala,
                "stars": row.price_stars,
            }
            for row in rows
        ],
        "charges": [
            {
                "id": c.charge_id,
                "order": str(c.order_id),
                "amount": c.amount,
                "state": c.state,
                "accepted": c.accepted,
            }
            for c in charges
        ],
    }


def totals(evidence):
    orders = evidence["orders"]
    charges = evidence["charges"]
    accepted = {c["order"] for c in charges if c["accepted"]}
    return {
        "active": len(orders),
        "test_credit": sum(o["halalas"] for o in orders if o["mode"] == "test_credit"),
        "unpaid": sum(o["mode"] == "stars" and o["id"] not in accepted for o in orders),
        "paid_stars": sum(c["amount"] for c in charges if c["state"] == "paid"),
        "refunds_in_progress": sum(
            c["state"] in {"refund_pending", "refunding", "refund_uncertain"} for c in charges
        ),
    }


async def validate_target(db, service, evidence, enabled):
    if service.enabled == enabled:
        raise ServiceError("admin_activation_changed")
    if not enabled:
        return
    if evidence["source_version"] != service.version:
        raise ServiceError("service_changed")
    if registry.types[service.slug].requires_ai and evidence["ai_state"] != "configured":
        raise ServiceError("provider_config")
    if config().stars_enabled and service.price_stars is None:
        raise ServiceError("admin_missing_stars_price")
    pending = await db.scalar(
        select(ServiceActivationTask.change_id)
        .join(ServiceActivationChange)
        .where(
            ServiceActivationChange.service_slug == service.slug,
            ServiceActivationTask.completed_at.is_(None),
        )
        .limit(1)
    )
    if pending:
        raise ServiceError("admin_activation_pending")


async def preview(slug, enabled, *, actor_id):
    authorize(actor_id)
    if type(enabled) is not bool:
        raise ServiceError("input_invalid")
    async with sessions() as db:
        service = await db.get(Service, slug)
        if service is None:
            raise ServiceError("unavailable")
        evidence = await snapshot(db, service)
        await validate_target(db, service, evidence, enabled)
        return evidence


@transaction_retry
async def change_activation(slug, enabled, *, actor_id, expected_hash, change_id):
    authorize(actor_id)
    if (
        type(enabled) is not bool
        or not isinstance(expected_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
    ):
        raise ServiceError("input_invalid")
    try:
        operation = UUID(str(change_id))
    except (ValueError, TypeError, AttributeError):
        raise ServiceError("input_invalid") from None
    async with sessions.begin() as db:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"activation:{operation}"},
        )
        # No customer/order locks under this service lock; admission uses customer→service.
        service = await db.scalar(select(Service).where(Service.slug == slug).with_for_update())
        if service is None:
            raise ServiceError("unavailable")
        previous = await db.get(ServiceActivationChange, operation)
        if previous:
            if (
                previous.actor_id,
                previous.service_slug,
                previous.new_enabled,
                previous.snapshot_hash,
            ) != (actor_id, slug, enabled, expected_hash):
                raise ServiceError("invalid_request")
            return previous.id  # Never reapply an old disable after later reactivation.
        evidence = await snapshot(db, service)
        if digest(evidence) != expected_hash:
            raise ServiceError("admin_activation_changed")
        await validate_target(db, service, evidence, enabled)
        db.add(
            ServiceActivationChange(
                id=operation,
                actor_id=actor_id,
                service_slug=slug,
                old_enabled=service.enabled,
                new_enabled=enabled,
                snapshot_hash=expected_hash,
                snapshot=evidence,
            )
        )
        service.enabled = enabled
        if enabled:
            await db.merge(
                Setting(key=f"CIRCUIT_RESET:{slug}", value={"value": datetime.now(UTC).isoformat()})
            )
        elif evidence["orders"]:
            await db.flush()  # Audit must precede its durable task's FK.
            db.add(ServiceActivationTask(change_id=operation))
        return operation


@transaction_retry
async def cancel_target(order_id):
    async with sessions.begin() as db:
        order = await lock_order(db, UUID(order_id))
        if order is not None:
            await fail_locked(db, order, "unavailable", cancelled=True)


@transaction_retry
async def complete_task(change_id):
    async with sessions.begin() as db:
        task = await db.get(ServiceActivationTask, change_id, with_for_update=True)
        if task and task.completed_at is None:
            task.completed_at = datetime.now(UTC)


async def settle_activations(ctx):
    async with sessions() as db:
        rows = list(
            (
                await db.scalars(
                    select(ServiceActivationChange)
                    .join(ServiceActivationTask)
                    .where(ServiceActivationTask.completed_at.is_(None))
                    .order_by(ServiceActivationChange.created_at, ServiceActivationChange.id)
                    .limit(5)
                )
            ).all()
        )
    for change in rows:
        # Intent's fixed IDs only. Existing settlement is terminal-safe and idempotent.
        for target in change.snapshot["orders"]:
            await cancel_target(target["id"])
        await complete_task(change.id)
