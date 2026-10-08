from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import Job, JobAttempt, Order, Service
from app.core.settings import config
from app.orders.engine import complete_locked, fail_locked
from app.orders.locking import lock_order
from app.orders.state import transition
from app.services.base import Result, ServiceError
from app.services.registry import registry


async def execute_job(ctx, job_id: str):
    async with sessions.begin() as db:
        reference = await db.get(Job, UUID(job_id))
        if not reference:
            return
        order = await lock_order(db, reference.order_id)
        job = await db.scalar(select(Job).where(Job.id == UUID(job_id)).with_for_update())
        if not job or job.status in {"done", "failed", "cancelled", "waiting"}:
            return
        now = datetime.now(UTC)
        if job.lease_until and job.lease_until > now:
            return
        if job.next_run_at > now:
            return
        if order.status in {"completed", "failed", "cancelled", "refunded"}:
            return
        service = await db.get(Service, order.service_slug)
        if not service or not service.enabled:
            await fail_locked(db, order, "unavailable", cancelled=True)
            return
        plugin = registry.types.get(order.service_slug)
        if not order.result and (not plugin or order.service_version != plugin.version):
            await fail_locked(db, order, "service_changed", cancelled=True)
            return
        if job.status == "running":
            job.failure_count += 1
            abandoned = await db.scalar(
                select(JobAttempt).where(
                    JobAttempt.job_id == job.id,
                    JobAttempt.number == job.attempts,
                    JobAttempt.status == "running",
                )
            )
            if abandoned:
                abandoned.status = "abandoned"
                abandoned.finished_at = now
                abandoned.error_key = "worker_interrupted"
        job.status, job.lease_until = "running", now + timedelta(minutes=10)
        if job.failure_count >= config().max_attempts:
            await fail_locked(db, order, "service_failed")
            return
        job.attempts += 1
        attempt_row = JobAttempt(job_id=job.id, number=job.attempts, status="running")
        db.add(attempt_row)
        await db.flush()
        attempt_id = attempt_row.id
        if order.status == "queued":
            transition(order, "processing")
        slug, inputs, cached = order.service_slug, order.inputs, order.result
        order_id, user_id = order.id, order.user_id
    from app.providers.runtime import runtime_for

    runtime = None
    result = None
    try:
        runtime = (
            ctx["runtime_factory"](job.id, user_id)
            if ctx.get("runtime_factory")
            else ctx.get("runtime")
            or runtime_for(
                job.id, user_id, needs_ai=not cached and registry.types[slug].needs_ai(inputs)
            )
        )
        result = (
            Result.model_validate(cached)
            if cached
            else await registry.get(slug, runtime).run(inputs)
        )
        if result.needs_confirmation:
            async with sessions.begin() as db:
                order = await lock_order(db, order_id)
                if order.status != "processing":
                    return
                order.result = result.model_dump(mode="json")
                transition(order, "waiting_confirmation")
                job = await db.scalar(select(Job).where(Job.order_id == order_id))
                job.status = "waiting"
                job.lease_until = None
                record = await db.get(JobAttempt, attempt_id)
                record.status = "waiting"
                record.finished_at = datetime.now(UTC)
            return
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            if order.status not in {"processing", "delivering"}:
                return
            if not order.result:
                order.result = result.model_dump(mode="json")
            transition(order, "delivering")
        await ctx["delivery"].send(user_id, order_id, result)
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            if order.status != "delivering":
                return
            await complete_locked(db, order)
            order.delivered_at = datetime.now(UTC)
            job = await db.scalar(select(Job).where(Job.order_id == order_id))
            job.status, job.lease_until = "done", None
            job.finished_at = datetime.now(UTC)
            record = await db.get(JobAttempt, attempt_id)
            record.status, record.finished_at = "done", datetime.now(UTC)
    except Exception as error:
        transient = isinstance(error, ServiceError) and error.transient
        transient = transient or (
            result is not None
            and isinstance(error, DBAPIError)
            and getattr(error.orig, "sqlstate", None) in {"40P01", "40001"}
        )
        # Delivery transports have their own retryable exceptions; never expose content.
        from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter

        transient = transient or isinstance(
            error, (TelegramNetworkError, TelegramRetryAfter, OSError)
        )
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            job = await db.scalar(select(Job).where(Job.order_id == order_id))
            job.lease_until = None
            if result is not None and not order.result:
                order.result = result.model_dump(mode="json")
            record = await db.get(JobAttempt, attempt_id)
            record.status, record.finished_at = "failed", datetime.now(UTC)
            record.error_key = error.key if isinstance(error, ServiceError) else "service_failed"
            job.failure_count += 1
            if transient and job.failure_count < config().max_attempts:
                job.status = "pending"
                job.next_run_at = datetime.now(UTC) + timedelta(seconds=15 * job.failure_count)
                if order.status == "processing":
                    transition(order, "queued")
            else:
                await fail_locked(
                    db, order, error.key if isinstance(error, ServiceError) else "service_failed"
                )

    finally:
        async with sessions() as db:
            final_order = await db.get(Order, order_id)
        if runtime is not None and final_order.status in {
            "completed",
            "failed",
            "cancelled",
            "refunded",
        }:
            from app.files.retention import cleanup_order_files

            try:
                await cleanup_order_files(order_id, runtime.storage)
            except Exception:
                pass  # The durable cleanup marker remains pending; delivery/finance already settled.
    from app.ops.circuit import evaluate

    await evaluate(slug, ctx.get("notifier"))
    if ctx.get("notifier"):
        async with sessions() as db:
            final = await db.get(Order, order_id)
        if final.error_key in {"provider_failed", "provider_invalid", "provider_usage"}:
            await ctx["notifier"].alert("provider_failure")
        if final.error_key in {"cost_cap", "user_cost_cap", "job_cost_cap"}:
            await ctx["notifier"].alert("daily_cost_cap")


async def dispatch(ctx):
    async with sessions() as db:
        cancelled_ids = list(
            (
                await db.scalars(
                    select(Order.id)
                    .join(Service, Service.slug == Order.service_slug)
                    .where(
                        Service.enabled.is_(False),
                        Order.status.in_(
                            ["queued", "processing", "waiting_confirmation", "delivering"]
                        ),
                    )
                )
            ).all()
        )
    for order_id in cancelled_ids:
        async with sessions.begin() as db:
            order = await lock_order(db, order_id)
            await fail_locked(db, order, "unavailable", cancelled=True)
    async with sessions() as db:
        now = datetime.now(UTC)
        ids = list(
            (
                await db.scalars(
                    select(Job.id).where(
                        Job.status.in_(["pending", "running"]), Job.next_run_at <= now
                    )
                )
            ).all()
        )
    for job_id in ids:
        await ctx["redis"].enqueue_job("execute_job", str(job_id), _job_id=f"job:{job_id}")


async def deliver_failures(ctx):
    from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

    async with sessions() as db:
        rows = list(
            (
                await db.execute(
                    select(Order.id, Order.user_id, Order.error_key)
                    .where(
                        Order.status.in_(["failed", "cancelled"]), Order.failure_notified.is_(False)
                    )
                    .limit(100)
                )
            ).all()
        )
    for order_id, user_id, key in rows:
        try:
            await ctx["delivery"].error(user_id, order_id, key or "service_failed")
        except (TelegramForbiddenError, TelegramBadRequest):
            pass  # User blocked/deleted the chat; there is no deliverable destination.
        except Exception:
            continue
        async with sessions.begin() as db:
            order = await db.get(Order, order_id)
            order.failure_notified = True


async def deliver_confirmations(ctx):
    async with sessions() as db:
        rows = list(
            (
                await db.execute(
                    select(Order.id, Order.user_id, Order.result)
                    .where(
                        Order.status == "waiting_confirmation",
                        Order.confirmation_notified.is_(False),
                    )
                    .limit(100)
                )
            ).all()
        )
    for order_id, user_id, result in rows:
        try:
            await ctx["delivery"].confirmation(user_id, order_id, result["preview"])
        except Exception:
            continue
        async with sessions.begin() as db:
            order = await db.get(Order, order_id)
            order.confirmation_notified = True
