from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Ledger, Order, User


class WalletError(Exception):
    key = "wallet_error"


class InsufficientFunds(WalletError):
    key = "insufficient"


@dataclass(frozen=True)
class Balance:
    available: int
    reserved: int

    @property
    def total(self):
        return self.available + self.reserved


def halalas(value: str | Decimal) -> int:
    try:
        number = Decimal(value)
        if not number.is_finite() or number <= 0 or number != number.quantize(Decimal(".01")):
            raise ValueError
        amount = int(number * 100)
        if amount > 10**12:
            raise ValueError
        return amount
    except (InvalidOperation, ValueError):
        raise WalletError from None


def sar(amount: int) -> str:
    return f"{Decimal(amount) / 100:.2f}"


async def balance(db: AsyncSession, user_id: int) -> Balance:
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(Ledger.available_delta), 0),
                func.coalesce(func.sum(Ledger.reserved_delta), 0),
            ).where(Ledger.user_id == user_id)
        )
    ).one()
    return Balance(int(row[0]), int(row[1]))


async def apply(
    db: AsyncSession, user_id: int, kind: str, amount: int, key: str, order_id: UUID | None = None
):
    if not db.in_transaction():
        raise RuntimeError("wallet requires an explicit transaction")
    if (
        type(amount) is not int
        or amount <= 0
        or amount > 10**12
        or kind not in {"credit", "reserve", "capture", "release", "refund"}
    ):
        raise WalletError
    user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise WalletError
    deltas = {
        "credit": (amount, 0),
        "reserve": (-amount, amount),
        "capture": (0, -amount),
        "release": (amount, -amount),
        "refund": (amount, 0),
    }
    available, reserved = deltas[kind]
    if not key or len(key) > 160:
        raise WalletError
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:wallet_key, 0))"), {"wallet_key": key}
    )
    existing = await db.scalar(select(Ledger).where(Ledger.idempotency_key == key))
    if existing:
        if (
            existing.user_id,
            existing.kind,
            existing.available_delta,
            existing.reserved_delta,
            existing.order_id,
        ) != (user_id, kind, available, reserved, order_id):
            raise WalletError
        return existing
    if kind == "credit" and order_id is not None:
        raise WalletError
    if kind != "credit":
        if order_id is None:
            raise WalletError
        order = await db.get(Order, order_id)
        if not order or order.user_id != user_id or order.price_halala != amount:
            raise WalletError
        entries = list((await db.scalars(select(Ledger).where(Ledger.order_id == order_id))).all())
        kinds = {entry.kind for entry in entries}
        if kind == "reserve" and kinds:
            raise WalletError
        reservation = next((entry for entry in entries if entry.kind == "reserve"), None)
        if kind in {"capture", "release", "refund"}:
            if (
                not reservation
                or reservation.user_id != user_id
                or reservation.reserved_delta != amount
            ):
                raise WalletError
        if kind in {"capture", "release"} and kinds & {"capture", "release"}:
            raise WalletError
        if kind == "refund" and ("capture" not in kinds or "refund" in kinds):
            raise WalletError
    funds = await balance(db, user_id)
    if funds.available + available < 0 or funds.reserved + reserved < 0:
        raise InsufficientFunds
    entry = Ledger(
        user_id=user_id,
        order_id=order_id,
        kind=kind,
        available_delta=available,
        reserved_delta=reserved,
        idempotency_key=key,
    )
    db.add(entry)
    await db.flush()
    return entry


async def reserve(db, user_id, amount, key, order_id):
    return await apply(db, user_id, "reserve", amount, key, order_id)


async def capture(db, user_id, amount, key, order_id):
    return await apply(db, user_id, "capture", amount, key, order_id)


async def release(db, user_id, amount, key, order_id):
    return await apply(db, user_id, "release", amount, key, order_id)
