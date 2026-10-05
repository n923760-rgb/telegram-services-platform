from sqlalchemy import or_, select

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.ops.settings import setting
from app.orders.engine import fail_locked
from app.orders.locking import lock_order


async def evaluate(slug, notifier=None):
    opened = False
    consecutive = False
    async with sessions.begin() as db:
        # Service row lock serializes disable/admission. Never hold it during an external call.
        service = await db.scalar(select(Service).where(Service.slug == slug).with_for_update())
        if not service:
            return False
        window = int(await setting(db, "CIRCUIT_WINDOW"))
        minimum = int(await setting(db, "CIRCUIT_MIN_SAMPLES"))
        threshold = float(await setting(db, "CIRCUIT_FAILURE_THRESHOLD"))
        count = int(await setting(db, "FAILURE_ALERT_COUNT"))
        from datetime import datetime

        reset = await setting(db, f"CIRCUIT_RESET:{slug}", default="1970-01-01T00:00:00+00:00")
        since = datetime.fromisoformat(reset)
        states = list(
            (
                await db.scalars(
                    select(Job.status)
                    .join(Order, Order.id == Job.order_id)
                    .where(
                        Order.service_slug == slug,
                        Job.finished_at >= since,
                        Job.status.in_(["done", "failed"]),
                        Order.status.in_(["completed", "refunded", "failed"]),
                        or_(
                            Order.error_key.is_(None),
                            Order.error_key.not_in(
                                [
                                    "image_unclear",
                                    "ocr_unclear",
                                    "input_invalid",
                                    "needs_information",
                                    "cost_cap",
                                    "user_cost_cap",
                                    "job_cost_cap",
                                    "provider_config",
                                ]
                            ),
                        ),
                    )
                    .order_by(Job.finished_at.desc(), Job.id.desc())
                    .limit(window)
                )
            ).all()
        )
        consecutive = len(states) >= count and all(s == "failed" for s in states[:count])
        if (
            service.enabled
            and len(states) >= minimum
            and states.count("failed") / len(states) >= threshold
        ):
            service.enabled = False
            opened = True
    if opened:
        # Release committed reservations in small transactions. Recovery repeats this sweep safely.
        async with sessions() as db:
            ids = list(
                (
                    await db.scalars(
                        select(Order.id).where(
                            Order.service_slug == slug,
                            Order.status.in_(
                                ["queued", "processing", "waiting_confirmation", "delivering"]
                            ),
                        )
                    )
                ).all()
            )
        for order_id in ids:
            async with sessions.begin() as db:
                order = await lock_order(db, order_id)
                await fail_locked(db, order, "circuit_paused", cancelled=True)
        if notifier:
            await notifier.alert("circuit_open", slug=slug)
    if consecutive and notifier:
        await notifier.alert("consecutive_failures", slug=slug)
    return opened
