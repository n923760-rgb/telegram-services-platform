"""Owner-authorized, bounded, metadata-only PostgreSQL order snapshot."""

import argparse
import asyncio
import json
import re
from collections import Counter
from datetime import UTC
from uuid import UUID

from sqlalchemy import select, text

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, JobAttempt, Ledger, Order, Setting, StarCharge
from app.ops.service_portfolio import owner_actor
from app.providers.runtime import provider
from app.services.base import ServiceError

MAX_ROWS = 64


def reference_bounds(value):
    if re.fullmatch(r"[a-fA-F0-9]{8}", value):
        return UUID(value + "0" * 24), UUID(value + "f" * 24)
    if re.fullmatch(r"[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}", value):
        return UUID(value), UUID(value)
    raise ServiceError("invalid_reference")


async def bounded_rows(db, statement):
    rows = (await db.execute(statement.limit(MAX_ROWS + 1))).all()
    if len(rows) > MAX_ROWS:
        raise ServiceError("diagnostic_limit")
    return rows


def wallet_evidence(mode, price, rows):
    counts = Counter(row.kind for row in rows)
    available = sum(row.available_delta for row in rows)
    reserved = sum(row.reserved_delta for row in rows)
    released = (
        mode == "test_credit"
        and type(price) is int
        and price > 0
        and counts == {"reserve": 1, "release": 1}
        and available == reserved == 0
        and all(
            (row.available_delta, row.reserved_delta)
            == ((-price, price) if row.kind == "reserve" else (price, -price))
            for row in rows
        )
    )
    return {
        "entry_counts": dict(sorted(counts.items())),
        "order_available_delta_halala": available,
        "order_reserved_delta_halala": reserved,
        "test_credit_release_confirmed": released,
    }


async def inspect(reference, actor_id=None):
    owner_actor(actor_id)  # Reject before any database access; never print actor/user IDs.
    lower, upper = reference_bounds(reference)
    async with sessions.begin() as db:
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        await db.execute(text("SET LOCAL statement_timeout = '5s'"))
        orders = (
            await db.execute(
                select(
                    Order.id,
                    Order.service_slug,
                    Order.service_version,
                    Order.status,
                    Order.error_key,
                    Order.payment_mode,
                    Order.price_halala,
                    Order.created_at,
                )
                .where(Order.id >= lower, Order.id <= upper)
                .order_by(Order.id)
                .limit(2)
            )
        ).all()
        if not orders:
            raise ServiceError("order_not_found")
        if len(orders) != 1:
            raise ServiceError("order_ambiguous")
        order = orders[0]
        job = (
            await db.execute(
                select(Job.id, Job.status, Job.attempts, Job.cost_sar).where(
                    Job.order_id == order.id
                )
            )
        ).one_or_none()
        ledger = await bounded_rows(
            db,
            select(Ledger.kind, Ledger.available_delta, Ledger.reserved_delta)
            .where(Ledger.order_id == order.id)
            .order_by(Ledger.id),
        )
        charges = await bounded_rows(
            db,
            select(StarCharge.state)
            .where(StarCharge.order_id == order.id)
            .order_by(StarCharge.charge_id),
        )
        holds, attempts = [], []
        if job:
            holds = await bounded_rows(
                db,
                select(
                    CostHold.id,
                    CostHold.created_at,
                    CostHold.status,
                    CostHold.amount,
                    CostUsage.cost_sar,
                    CostUsage.input_tokens,
                    CostUsage.output_tokens,
                )
                .outerjoin(CostUsage, CostUsage.hold_id == CostHold.id)
                .where(CostHold.job_id == job.id)
                .order_by(CostHold.created_at, CostHold.id),
            )
            attempts = await bounded_rows(
                db,
                select(JobAttempt.number, JobAttempt.status, JobAttempt.error_key)
                .where(JobAttempt.job_id == job.id)
                .order_by(JobAttempt.number),
            )
        pause_row = (
            await db.execute(select(Setting.value).where(Setting.key == "PROVIDER_PAUSED"))
        ).one_or_none()
        pause = pause_row[0] if pause_row is not None else {"value": False}
        if not isinstance(pause, dict) or type(pause.get("value")) is not bool:
            raise ServiceError("provider_state_invalid")
        paused = pause["value"]
        provider_config = {"paused": paused}
        try:
            adapter = provider()
            provider_config.update(
                output_limit=adapter.max_output_tokens, limit_field=adapter.output_limit_field()
            )
        except (ValueError, AttributeError):
            provider_config["configuration"] = "unavailable"
        costs = [
            {
                "hold_id": str(row.id),
                "created_at_utc": row.created_at.astimezone(UTC).isoformat(),
                "status": row.status,
                "reserved_sar": str(row.amount),
                "recorded_sar": str(row.cost_sar) if row.cost_sar is not None else None,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "recorded_overrun": row.cost_sar > row.amount if row.cost_sar is not None else None,
            }
            for row in holds
        ]
        return {
            "status": "observed",
            "request": str(order.id)[:8],
            "service": order.service_slug,
            "version": order.service_version,
            "order_status": order.status,
            "error_key": order.error_key,
            "created_at_utc": order.created_at.astimezone(UTC).isoformat(),
            "payment_mode": order.payment_mode,
            "wallet": wallet_evidence(order.payment_mode, order.price_halala, ledger),
            "stars_charge_states": dict(sorted(Counter(row.state for row in charges).items())),
            "job": {
                "status": job.status,
                "attempts": job.attempts,
                "recorded_cost_sar": str(job.cost_sar),
            }
            if job
            else None,
            "attempts": [dict(row._mapping) for row in attempts],
            "cost_holds": costs,
            "provider": provider_config,
            "observations": {
                "unsettled_cost_holds": sum(row.status in {"open", "uncertain"} for row in holds),
                "recorded_overruns": sum(row["recorded_overrun"] is True for row in costs),
            },
            "qualification": "database_snapshot_only; provider_invoice_not_verified",
            "actions_performed": [],
        }


def main():
    parser = argparse.ArgumentParser(description="Read-only, owner-authorized order diagnostics.")
    parser.add_argument("reference", help="Eight hexadecimal characters or a full order UUID.")
    parser.add_argument(
        "--actor", type=int, help="Configured admin ID when there are multiple owners."
    )
    args = parser.parse_args()
    try:
        report = asyncio.run(inspect(args.reference, args.actor))
    except ServiceError as error:
        report = {"status": "blocked", "error": error.key}
    except Exception:
        report = {"status": "unknown", "error": "runtime_unavailable"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "observed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
