"""Owner-only preparation of a synthetic cap probe; never sends a provider request."""

import argparse
import asyncio
import json
from hashlib import sha256
from urllib.parse import urlsplit

from sqlalchemy import select, text

from app.builders.schema import StrictModel
from app.core.db import sessions
from app.core.models import Setting
from app.ops.service_portfolio import owner_actor
from app.providers.runtime import provider
from app.services.base import ServiceError


class Outcome(StrictModel):
    ok: bool


async def prepare(actor_id=None):
    owner_actor(actor_id)
    adapter = provider()
    if not callable(getattr(adapter, "request_body", None)):
        raise ServiceError("provider_config")
    adapter.max_output_tokens = min(adapter.max_output_tokens, 128)
    schema = Outcome.model_json_schema()
    source = "Synthetic system verification. No customer content."
    prompt = 'Return exactly {"ok":true}.'
    bound = adapter.upper_bound(schema, source, prompt, [])
    body = adapter.request_body(schema, source, prompt, [])
    async with sessions.begin() as db:
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        await db.execute(text("SET LOCAL statement_timeout = '5s'"))
        row = (
            await db.execute(select(Setting.value).where(Setting.key == "PROVIDER_PAUSED"))
        ).one_or_none()
        value = row[0] if row else {"value": False}
        if not isinstance(value, dict) or type(value.get("value")) is not bool:
            raise ServiceError("provider_state_invalid")
    return {
        "status": "prepared",
        "provider_paused": value["value"],
        "host": urlsplit(adapter.cfg.ai_base_url).hostname,
        "model": body["model"],
        "limit_field": adapter.output_limit_field(),
        "probe_output_limit": adapter.max_output_tokens,
        "calculated_reservation_bound_sar": str(bound),
        "body_sha256": sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(),
        "live_execution": "not_performed",
        "qualification": "request_preparation_only; no_provider_cap_or_invoice_verification",
        "actions_performed": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=int)
    args = parser.parse_args()
    try:
        report = asyncio.run(prepare(args.actor))
    except ServiceError as error:
        report = {"status": "blocked", "error": error.key}
    except Exception:
        report = {"status": "unknown", "error": "runtime_unavailable"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "prepared" else 1


if __name__ == "__main__":
    raise SystemExit(main())
