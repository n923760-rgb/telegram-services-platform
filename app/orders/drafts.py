"""One unsubmitted request contract for chat and Mini App intake; no purchase."""

from uuid import uuid4

from app.core.settings import config
from app.payments.stars import terms_hash


def new_draft(service, *, inputs=None, index=0):
    cfg = config()
    return {
        "slug": service.slug,
        "name_ar": service.name_ar,
        "name_en": service.name_en,
        "schema": service.input_schema,
        "price": service.price_halala,
        "version": service.version,
        "inputs": inputs or {},
        "index": index,
        "key": uuid4().hex,
        "payment_mode": "stars" if cfg.stars_enabled else "test_credit",
        "stars_price": service.price_stars if cfg.stars_enabled else None,
        "terms_version": cfg.stars_terms_version if cfg.stars_enabled else None,
        "terms_hash": terms_hash() if cfg.stars_enabled else None,
        "terms": {"ar": cfg.stars_terms_ar, "en": cfg.stars_terms_en},
    }
