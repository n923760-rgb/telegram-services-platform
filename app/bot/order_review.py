"""Read-only, bounded draft review; admission and settlement remain in orders.

Optional <prompt_key>_review catalog entries provide short labels without changing
persisted service schemas. New/unknown prompts fall back to numbered input labels.
Never render upload keys or bulk customer text. This is an input summary, not a
validated output preview: generation and final admission have not happened yet.
"""

import unicodedata

from app.core.i18n import CATALOGS, tr
from app.services.base import InputSchema, active_field, get_input
from app.wallet.ledger import sar


def _units(text):
    return len(text.encode("utf-16-le")) // 2


def _inline(value, limit=80):
    # Keep user-provided titles/page orders inside one quoted row; formatting and
    # direction controls cannot insert a fabricated price or confirmation line.
    value = " ".join(
        "".join(c for c in value if unicodedata.category(c) not in {"Cc", "Cf"}).split()
    )
    return value if len(value) <= limit else value[: limit - 1] + "…"


def input_summary(schema, inputs, lang, budget=1000):
    rows = []
    for number, field in enumerate(schema.conversation(), 1):
        if not active_field(field, inputs):
            continue
        value = get_input(inputs, field.name)
        if value is None:
            if field.required:
                continue  # Final admission still rejects incomplete drafts.
            display = _inline(
                tr(
                    "review_not_specified" if field.skip_key == "skip_field" else field.skip_key,
                    lang,
                )
            )
        elif field.kind in {"image", "file", "audio"}:
            display = tr("review_upload_count", lang, count=len(value) if field.multiple else 1)
        elif field.choices and value in field.choices:
            display = _inline(tr(field.choice_keys[field.choices.index(value)], lang))
        elif field.single_line and isinstance(value, str):
            display = "«" + _inline(value) + "»"
        elif isinstance(value, str):
            display = tr("review_text_size", lang, count=len(value))
        else:
            continue
        label_key = field.prompt_key + "_review"
        label = (
            tr(label_key, lang)
            if label_key in CATALOGS.get(lang, CATALOGS["ar"])
            else tr("review_field", lang, number=number)
        )
        rows.append(_inline(label, 40) + ": " + display)
    if not rows:
        return ""
    result = tr("review_heading", lang)
    for index, row in enumerate(rows):
        # Reserve space for a complete omitted-fields notice, never a cut row.
        remaining = len(rows) - index - 1
        suffix = "\n" + tr("review_omitted", lang, count=remaining) if remaining else ""
        if _units(result + "\n" + row + suffix) > budget:
            notice = "\n" + tr("review_omitted", lang, count=len(rows) - index)
            return result + notice if _units(result + notice) <= budget else ""
        result += "\n" + row
    return result


def confirmation_text(data, lang):
    title = tr("confirmation_title", lang, name=data.get(f"name_{lang}", data["slug"]))
    payment = (
        tr("stars_confirm", lang, amount=data["stars_price"], terms=data["terms"][lang])
        if data.get("payment_mode") == "stars"
        else tr("confirm_price", lang, amount=sar(data["price"]))
    )
    # Terms may occupy 2500 UTF-16 units. Keep the original full terms and price;
    # only the optional summary shrinks to fit Telegram's message limit.
    budget = min(1000, max(0, 3900 - _units(title + "\n\n" + payment) - 2))
    summary = input_summary(
        InputSchema.model_validate(data["schema"]), data["inputs"], lang, budget
    )
    return title + ("\n\n" + summary if summary else "") + "\n\n" + payment
