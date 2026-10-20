"""Local worker inventory and owner-authorized, individually audited enablement."""

import argparse
import asyncio
import json
from uuid import uuid4

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Service, ServiceActivationChange, ServiceActivationTask
from app.core.settings import config
from app.ops import activation
from app.ops.readiness import ai_configuration
from app.ops.worker_capabilities import probe_worker
from app.services.base import ServiceError, ai_policy
from app.services.registry import _input_contract, registry

MAX_SERVICES = 64


def customer_slugs():
    slugs = sorted(slug for slug in registry.types if registry.can_request(slug))
    if not slugs or len(slugs) > MAX_SERVICES:
        raise ServiceError("portfolio_limit")
    return slugs


def owner_actor(actor_id=None):
    if actor_id is None:
        admins = config().admin_ids
        if len(admins) != 1:
            raise ServiceError("choose_configured_admin")
        actor_id = admins[0]
    activation.authorize(actor_id)
    return actor_id


async def inspect():
    capabilities = await probe_worker()
    slugs = customer_slugs()
    cfg = config()
    targets, services = [], []
    async with sessions() as db:
        rows = {
            row.slug: row
            for row in await db.scalars(select(Service).where(Service.slug.in_(slugs)))
        }
        pending = set(
            await db.scalars(
                select(ServiceActivationChange.service_slug)
                .distinct()
                .join(ServiceActivationTask)
                .where(
                    ServiceActivationTask.completed_at.is_(None),
                    ServiceActivationChange.service_slug.in_(slugs),
                )
            )
        )
        ai_state = await ai_configuration(db)
        for slug in slugs:
            plugin, row = registry.types[slug], rows.get(slug)
            requirements = list(plugin.worker_requirements)
            if cfg.document_visual_review and "office_export" in requirements:
                requirements.append("pdf_previews")
            blockers = [
                "worker_missing:" + key for key in requirements if not capabilities.get(key)
            ]
            warnings = [
                "worker_optional_missing:" + key
                for key in plugin.optional_worker_requirements
                if not capabilities.get(key)
            ]
            if plugin.optional_ai and ai_state != "configured":
                warnings.append("ai_options_unavailable")
            evidence = None
            if row is None:
                blockers.append("service_missing")
            else:
                if row.version != plugin.version or _input_contract(
                    row.input_schema
                ) != _input_contract(plugin.input_schema.model_dump()):
                    blockers.append("service_changed")
                if plugin.requires_ai and ai_state != "configured":
                    blockers.append("provider_config")
                if cfg.stars_enabled and row.price_stars is None:
                    blockers.append("admin_missing_stars_price")
                if slug in pending:
                    blockers.append("admin_activation_pending")
                try:
                    evidence = await activation.snapshot(db, row)
                    if not row.enabled and not blockers:
                        await activation.validate_target(db, row, evidence, True)
                        targets.append((slug, activation.digest(evidence)))
                except ServiceError as error:
                    blockers.append(error.key)
            services.append(
                {
                    "slug": slug,
                    "name_ar": plugin.name_ar,
                    "version": plugin.version,
                    "stored_version": row.version if row else None,
                    "enabled": row.enabled if row else False,
                    "price_halala": row.price_halala if row else None,
                    "price_stars": row.price_stars if row else None,
                    "ai_required": plugin.requires_ai,
                    "ai_policy": ai_policy(plugin),
                    "worker_requirements": requirements,
                    "active_orders": len(evidence["orders"]) if evidence is not None else None,
                    "blockers": sorted(set(blockers)),
                    "warnings": warnings,
                }
            )
    return {
        "status": "ready" if all(not row["blockers"] for row in services) else "blocked",
        "payment_mode": "stars" if cfg.stars_enabled else "test_credit",
        "ai_state": ai_state,
        "worker_capabilities": capabilities,
        "customer_services": len(services),
        "services": services,
        "qualification": "local_configuration_only; live_provider/mobile_quality_not_certified",
    }, targets


async def enable_all(actor_id=None):
    actor = owner_actor(actor_id)
    report, targets = await inspect()
    report["newly_enabled"] = []
    if report["status"] != "ready":
        return report  # No changes if any initial check fails.
    for slug, expected in targets:
        try:
            await activation.change_activation(
                slug, True, actor_id=actor, expected_hash=expected, change_id=uuid4()
            )
        except ServiceError as error:
            report.update(
                status="partial" if report["newly_enabled"] else "blocked",
                stopped_service=slug,
                error=error.key,
            )
            return report
        report["newly_enabled"].append(slug)
        for row in report["services"]:
            if row["slug"] == slug:
                row["enabled"] = True
    report["status"] = "enabled"
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Inspect customer services; --enable uses configured owner authorization and audited activation."
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable all eligible customer services after a complete preflight; no price/payment changes.",
    )
    parser.add_argument(
        "--actor",
        type=int,
        help="Configured Telegram administrator ID; required only if ADMIN_IDS is not a single owner.",
    )
    args = parser.parse_args()
    try:
        if args.enable:
            report = asyncio.run(enable_all(args.actor))
        else:
            report, _ = asyncio.run(inspect())
    except ServiceError as error:
        report = {"status": "blocked", "error": error.key}
    except Exception:
        # A connection failure after commit can have an unknown write outcome.
        # Rerun inspection before retry; never print exception/configuration bodies.
        report = {"status": "unknown", "error": "runtime_unavailable"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"ready", "enabled"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
