"""Bounded service browsing from registered presentation metadata, not slug branches."""

import re

from app.core.i18n import tr
from app.services.base import ai_policy
from app.services.catalog import CATEGORY_KEYS, ordered
from app.services.registry import registry

SERVICE_PAGE_SIZE = 6


def parse_callback(data):
    match = re.fullmatch(r"catalog:([a-z]+):(0|[1-9][0-9]{0,5})", data or "")
    if not match or match[1] not in CATEGORY_KEYS:
        return None
    return match[1], int(match[2])


def view(rows, lang, *, category=None, page=0, admin=False, ai_available=True):
    groups = {key: [] for key in CATEGORY_KEYS}
    for service in ordered(rows, registry.types):
        cls = registry.types.get(service.slug)
        if getattr(cls, "admin_only", False) and admin is not True:
            continue
        if getattr(cls, "replaced_by", None) is not None:
            continue
        key = getattr(cls, "category", "other")
        groups[key if key in groups else "other"].append(service)

    def notice(values):
        return (
            "\n\n" + tr("catalog_ai_notice", lang)
            if not ai_available
            and any(ai_policy(registry.types.get(s.slug)) != "none" for s in values)
            else ""
        )

    if category is None:
        items = [
            (tr(CATEGORY_KEYS[key], lang), f"catalog:{key}:0")
            for key, values in groups.items()
            if values
        ]
        return (
            tr("catalog_choose" if items else "no_services", lang)
            + notice([s for values in groups.values() for s in values]),
            items,
        )
    if category not in groups:
        raise ValueError("invalid category")
    values = groups[category]
    if not values:
        return tr("catalog_empty", lang), [(tr("catalog_back", lang), "menu:services")]
    pages = (len(values) + SERVICE_PAGE_SIZE - 1) // SERVICE_PAGE_SIZE
    page = max(0, min(page, pages - 1))
    visible = values[page * SERVICE_PAGE_SIZE : (page + 1) * SERVICE_PAGE_SIZE]
    items = [(s.name_ar if lang == "ar" else s.name_en, f"service:{s.slug}") for s in visible]
    text = (
        tr(CATEGORY_KEYS[category], lang)
        + "\n\n"
        + tr(CATEGORY_KEYS[category] + "_description", lang)
    )
    text += "\n\n" + tr("choose_service", lang)
    text += notice(values)
    if pages > 1:
        text += "\n\n" + tr("catalog_page", lang, page=page + 1, pages=pages)
        if page:
            items.append((tr("catalog_previous", lang), f"catalog:{category}:{page - 1}"))
        if page + 1 < pages:
            items.append((tr("catalog_next", lang), f"catalog:{category}:{page + 1}"))
    items.append((tr("catalog_back", lang), "menu:services"))
    return text, items
