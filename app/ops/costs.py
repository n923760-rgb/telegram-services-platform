from datetime import datetime
from decimal import ROUND_UP, Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core.db import sessions
from app.core.models import CostBudget, CostHold, CostUsage, Job
from app.core.transactions import transaction_retry
from app.ops.settings import decimal_setting, setting
from app.services.base import ServiceError

UNIT = Decimal(".000001")


def keys(user_id, day=None):
    day = day or datetime.now(ZoneInfo("Asia/Riyadh")).date().isoformat()
    return f"global:{day}", f"user:{user_id}:{day}"


async def locked_budget(db, key):
    await db.execute(
        insert(CostBudget).values(key=key, spent=0, reserved=0).on_conflict_do_nothing()
    )
    return await db.scalar(select(CostBudget).where(CostBudget.key == key).with_for_update())


async def check_admission(db, user_id):
    global_key, user_key = keys(user_id)
    for key, limit_name, error_key in [
        (global_key, "MAX_DAILY_COST_SAR", "cost_cap"),
        (user_key, "MAX_COST_PER_USER_PER_DAY", "user_cost_cap"),
    ]:
        budget = await locked_budget(db, key)
        if budget.spent + budget.reserved >= await decimal_setting(db, limit_name):
            raise ServiceError(error_key)


@transaction_retry
async def reserve_call(job_id: UUID, user_id: int, bound: Decimal) -> UUID:
    if not bound.is_finite() or bound <= 0:
        raise ServiceError("provider_config")
    bound = bound.quantize(UNIT, rounding=ROUND_UP)
    if bound <= 0:
        raise ServiceError("provider_config")
    async with sessions.begin() as db:
        if await setting(db, "PROVIDER_PAUSED", default=False):
            raise ServiceError("provider_usage")
        global_key, user_key = keys(user_id)
        global_budget = await locked_budget(db, global_key)
        user_budget = await locked_budget(db, user_key)
        job = await db.scalar(select(Job).where(Job.id == job_id).with_for_update())
        if not job or job.status != "running":
            raise ServiceError("unavailable")
        open_cost = await db.scalar(
            select(func.coalesce(func.sum(CostHold.amount), 0)).where(
                CostHold.job_id == job_id, CostHold.status.in_(["open", "uncertain"])
            )
        )
        if job.cost_sar + open_cost + bound > await decimal_setting(db, "MAX_JOB_COST_SAR"):
            raise ServiceError("job_cost_cap")
        if global_budget.spent + global_budget.reserved + bound > await decimal_setting(
            db, "MAX_DAILY_COST_SAR"
        ):
            raise ServiceError("cost_cap")
        if user_budget.spent + user_budget.reserved + bound > await decimal_setting(
            db, "MAX_COST_PER_USER_PER_DAY"
        ):
            raise ServiceError("user_cost_cap")
        global_budget.reserved += bound
        user_budget.reserved += bound
        hold = CostHold(
            id=uuid4(),
            job_id=job_id,
            global_key=global_key,
            user_key=user_key,
            amount=bound,
            status="open",
        )
        db.add(hold)
        return hold.id


@transaction_retry
async def settle_call(
    hold_id,
    cost: Decimal,
    input_tokens=0,
    output_tokens=0,
    *,
    provider="unknown",
    model="unknown",
    rates=None,
):
    if (
        not cost.is_finite()
        or cost < 0
        or type(input_tokens) is not int
        or type(output_tokens) is not int
        or min(input_tokens, output_tokens) < 0
    ):
        raise ServiceError("provider_usage")
    cost = cost.quantize(UNIT, rounding=ROUND_UP)
    if len(provider) > 80 or len(model) > 120:
        raise ServiceError("provider_usage")
    async with sessions.begin() as db:
        info = await db.get(CostHold, hold_id)
        if not info:
            raise ServiceError("invalid_request")
        global_budget = await locked_budget(db, info.global_key)
        user_budget = await locked_budget(db, info.user_key)
        hold = await db.scalar(select(CostHold).where(CostHold.id == hold_id).with_for_update())
        existing = await db.scalar(select(CostUsage).where(CostUsage.hold_id == hold_id))
        if existing:
            if existing.cost_sar != cost:
                raise ServiceError("provider_usage")
            return
        job = await db.scalar(select(Job).where(Job.id == hold.job_id).with_for_update())
        for budget in (global_budget, user_budget):
            budget.reserved -= hold.amount
            budget.spent += cost
        hold.status = "settled"
        job.cost_sar += cost
        db.add(
            CostUsage(
                hold_id=hold_id,
                job_id=job.id,
                cost_sar=cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=provider,
                model=model,
                rate_snapshot=rates or {},
            )
        )
    if cost > info.amount:
        # A provider/model pricing contract changed: stop future calls, preserve the actual charge.
        from app.core.models import Setting

        async with sessions.begin() as db:
            await db.merge(Setting(key="PROVIDER_PAUSED", value={"value": True}))
        raise ServiceError("provider_usage")


@transaction_retry
async def uncertain_call(hold_id):
    async with sessions.begin() as db:
        hold = await db.get(CostHold, hold_id)
        if hold and hold.status == "open":
            hold.status = "uncertain"
    # Keep exposure held until a human reconciles provider billing; never fabricate zero cost.
