from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import CostHold, CostUsage, Job, Ledger, Order, User


async def report(day=None):
    zone = ZoneInfo("Asia/Riyadh")
    day = day or datetime.now(zone).date()
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    end = start + timedelta(days=1)
    async with sessions() as db:
        count = await db.scalar(
            select(func.count(Order.id)).where(Order.created_at >= start, Order.created_at < end)
        )
        captured = await db.scalar(
            select(func.coalesce(func.sum(-Ledger.reserved_delta), 0)).where(
                Ledger.kind == "capture", Ledger.created_at >= start, Ledger.created_at < end
            )
        )
        refunds = await db.scalar(
            select(func.coalesce(func.sum(Ledger.available_delta), 0)).where(
                Ledger.kind == "refund", Ledger.created_at >= start, Ledger.created_at < end
            )
        )
        releases = await db.scalar(
            select(func.coalesce(func.sum(Ledger.available_delta), 0)).where(
                Ledger.kind == "release", Ledger.created_at >= start, Ledger.created_at < end
            )
        )
        costs = await db.scalar(
            select(func.coalesce(func.sum(CostUsage.cost_sar), 0))
            .join(CostHold, CostHold.id == CostUsage.hold_id)
            .where(CostHold.created_at >= start, CostHold.created_at < end)
        )
        pending_cost = await db.scalar(
            select(func.coalesce(func.sum(CostHold.amount), 0)).where(
                CostHold.created_at >= start,
                CostHold.created_at < end,
                CostHold.status.in_(["open", "uncertain"]),
            )
        )
        failures = await db.scalar(
            select(func.count(Job.id))
            .join(Order, Order.id == Job.order_id)
            .where(Job.status == "failed", Job.finished_at >= start, Job.finished_at < end)
        )
        users = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= start, User.created_at < end)
        )
        top = list(
            (
                await db.execute(
                    select(Order.service_slug, func.count(Order.id))
                    .where(Order.created_at >= start, Order.created_at < end)
                    .group_by(Order.service_slug)
                    .order_by(func.count(Order.id).desc())
                    .limit(5)
                )
            ).all()
        )
    revenue = Decimal(captured - refunds) / 100
    return tr(
        "daily_report",
        day=day,
        orders=count,
        revenue=f"{revenue:.2f}",
        cost=f"{costs:.6f}",
        pending=f"{pending_cost:.6f}",
        margin=f"{revenue - costs:.2f}",
        failed=failures,
        refunded=f"{Decimal(refunds) / 100:.2f}",
        released=f"{Decimal(releases) / 100:.2f}",
        captured=f"{Decimal(captured) / 100:.2f}",
        users=users,
        top="، ".join(f"{slug}: {n}" for slug, n in top) or tr("none"),
    )


async def flush_reports(ctx):
    """Recover report sends without permanently marking a failed send as delivered."""
    from datetime import date
    from uuid import uuid4

    redis = ctx["redis"]
    async for raw_key in redis.scan_iter(match="report:pending:*"):
        key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
        day = date.fromisoformat(key.rsplit(":", 1)[1])
        sent_key = f"report:sent:{day}"
        if await redis.exists(sent_key):
            await redis.delete(key)
            continue
        claim_key = f"report:claim:{day}"
        token = uuid4().hex
        if not await redis.set(claim_key, token, nx=True, ex=120):
            continue
        try:
            await ctx["notifier"].channel.send("report_message", content=await report(day))
            await redis.set(sent_key, "sent", ex=604800)
            await redis.delete(key)
        finally:
            await redis.eval(
                "if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0",
                1,
                claim_key,
                token,
            )


async def daily_report(ctx):
    day = datetime.now(ZoneInfo("Asia/Riyadh")).date()
    await ctx["redis"].set(f"report:pending:{day}", "due", nx=True, ex=604800)
    await flush_reports(ctx)
