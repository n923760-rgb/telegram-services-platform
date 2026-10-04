"""Operator-only CLI after comparing a cost hold against provider billing."""

import asyncio
import sys
from decimal import Decimal
from uuid import UUID

from app.ops.costs import settle_call


async def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m app.ops.reconcile HOLD_UUID CONFIRMED_COST_SAR")
    cost = Decimal(sys.argv[2])
    if not cost.is_finite() or cost < 0:
        raise SystemExit("Cost must be a nonnegative finite Decimal")
    await settle_call(UUID(sys.argv[1]), cost)


if __name__ == "__main__":
    asyncio.run(main())
