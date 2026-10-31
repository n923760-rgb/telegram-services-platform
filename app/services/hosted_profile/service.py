"""Administrative qualification only; never enabled or sold to customers by default."""

import asyncio
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from app.core.i18n import tr, translations
from app.core.settings import config
from app.publications import fulfillment, prepared_page
from app.publications.offering import CONTRACT, PRICE_HALALA
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.hosted_profile.schema import Inputs


class HostedProfile(BaseService):
    slug = "hosted_profile"
    version = "1"
    category = "professional"
    menu_order = 35
    admin_only = True
    enabled_by_default = False
    requires_ai = True
    name_ar = tr("hosted_profile_name")
    name_en = tr("hosted_profile_name", "en")
    description_ar = tr("hosted_profile_description")
    price_sar = Decimal(PRICE_HALALA) / 100
    purchase_contract = CONTRACT
    worker_requirements = ("pdf_font",)
    input_schema = InputSchema(
        fields=[
            InputField(
                name="language",
                prompt_key="hosted_profile_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(
                name="name", prompt_key="hosted_profile_person", single_line=True, max_length=64
            ),
            InputField(
                name="role", prompt_key="hosted_profile_role", single_line=True, max_length=96
            ),
            InputField(name="intro", prompt_key="hosted_profile_intro", max_length=480),
            InputField(
                name="phone",
                prompt_key="hosted_profile_phone",
                single_line=True,
                max_length=32,
                required=False,
            ),
            InputField(
                name="links", prompt_key="hosted_profile_links", max_length=2100, required=False
            ),
            InputField(
                name="sections",
                prompt_key="hosted_profile_sections",
                max_length=5000,
                required=False,
            ),
            InputField(name="brief", prompt_key="hosted_profile_brief", max_length=1600),
            InputField(
                name="qr",
                prompt_key="hosted_profile_qr",
                choices=["embedded", "separate"],
                choice_keys=["hosted_profile_qr_embedded", "hosted_profile_qr_separate"],
            ),
        ]
    )

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        cfg = config()
        if not cfg.publications_enabled:
            raise ServiceError("unavailable")
        if self.runtime.ai is None:
            raise ServiceError("service_ai_unavailable")
        identity = uuid4()
        try:
            completion = await fulfillment.generate(
                self.runtime.ai,
                values.profile(),
                values.brief,
                publication_id=identity,
                origin=cfg.publication_origin,
                embedded_qr=values.qr == "embedded",
            )
            # Internal generation is already bounded by worker concurrency. The
            # anonymous/owner HTTP render slots must not discard a paid AI plan.
            files = await asyncio.to_thread(
                prepared_page.render,
                completion.payload,
                publication_id=identity,
                origin=cfg.publication_origin,
            )
        except (ValidationError, ValueError):
            raise ServiceError("provider_invalid") from None

        # Ordinary owner-bound deliverables and durable handoff are persisted by
        # the existing order runner. Retry delivery uses that result, not AI.
        def save():
            types = {
                "profile.html": "text/html",
                "qr.png": "image/png",
                "qr.svg": "image/svg+xml",
                "share-card.png": "image/png",
            }
            return [
                self.runtime.storage.save(name, data, types[name]) for name, data in files.items()
            ]

        artifacts = await asyncio.to_thread(save)
        return Result(
            preview=tr("hosted_profile_pilot_preview", values.language),
            preview_localizations=translations("hosted_profile_pilot_preview"),
            artifacts=artifacts,
            completion=completion,
        )


SERVICE = HostedProfile
