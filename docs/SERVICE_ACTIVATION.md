# Staged service activation and development

Owner update, 2026-10-13: develop and enable all current customer services. The
registry contains 16 customer outcomes, one private verification utility and one
retired OCR product. Use the owner-authorized audited portfolio command below;
source qualification still differs from real deployment, provider/mobile quality
acceptance and paid launch. Keep payment configuration last. Preserve default
flags and DB-owned prices; do not bypass activation gates through raw SQL.

## All-current-service inspection and activation

Run these only after deploying the reviewed source and migrating the installation.
Use the **worker**, because the lean bot/API images do not contain native programs.

```bash
cd /srv/ai-dev-lab/projects/telegram-services-platform
docker compose exec -T worker python -m app.ops.service_portfolio
docker compose exec -T worker python -m app.ops.service_portfolio --enable
```

The first command is read-only. It lists each public canonical service, source/DB
versions, existing SAR test-credit/Stars prices, active-order count, local AI state,
declared worker requirements, blockers and optional-tool warnings. No customer
content, order IDs, endpoints or credentials are printed. Native probes inspect
fixed programs/language packs/imports/fonts; they are not output-quality trials.

`--enable` authorizes the sole configured ADMIN_IDS entry automatically. If there
are multiple administrators, pass `--actor TELEGRAM_ADMIN_ID`; it must already be
configured. No role is granted. Private/retired plugins are excluded dynamically.
Each service's immutable audit records its actor and frozen activation snapshot.
Input/schema mismatch, required AI off/pause/config error, missing worker tools,
required Stars price or pending cancellation blocks the initial batch with **no
activation writes**. Native OCR is optional for the configured-AI image-text path;
an unavailable local engine is disclosed, while existing AI fallback stays bounded.
Visual review additionally needs its native preview package when configured.

Changes use existing per-service transactions and stale-fingerprint checks. A
concurrent change can stop after earlier services succeeded: `partial` reports
those services, not all-or-nothing success. Inspect again before retry. Already
enabled services are skipped without new audit/reset operations. A DB connection
failure can leave an unknown commit outcome; the redacted CLI reports `unknown`
and never claims no writes. The command does not disable services, change prices,
modify provider/payment flags, reserve/capture balances or generate customer work.

At most 64 public services, 100 active orders/500 receipts per service are inspected.
`enabled` means the inspected activation operations completed; runtime/configuration
can change later and new requests still use ordinary admission/financial gates.
Representative real-provider/mobile acceptance below remains necessary for quality
claims. Historical staged guidance is retained as the acceptance sequence.

## Read-only deployed inventory

Run from `/srv/ai-dev-lab/projects/telegram-services-platform` on the VPS. This
prints service metadata only, not secrets, orders, prompts or customer content.
The AI flag means configured activation, not provider connectivity/quality.

```bash
docker compose exec -T api python - <<'PY'
import asyncio
from sqlalchemy import select
from app.core.db import sessions
from app.core.models import Service
from app.core.settings import config
from app.services.registry import registry

async def main():
    print('AI_ENABLED:', config().ai_enabled)
    async with sessions() as db:
        for row in await db.scalars(select(Service).order_by(Service.slug)):
            plugin = registry.types.get(row.slug)
            visible = registry.customer_visible(row.slug)
            print(row.slug, row.name_ar,
                  'enabled=' + str(row.enabled),
                  'visible=' + str(visible),
                  'version=' + row.version,
                  'source=' + (plugin.version if plugin else 'missing'), sep=' | ')

asyncio.run(main())
PY
```

## Trial/acceptance order

Use isolated administrator test-credit trials, not customer paid launch. Source
regression/native gates have run; representative outputs still need review in the
actual deployed worker and target mobile apps. Exercise one service at a time
after technical activation, retain prices, record its output acceptance, and stop
the affected service on failure.
`/enable SLUG` validates existing activation policy; it is not a quality certificate.
`/disable SLUG` also cancels unsettled orders, so review their impact before using it.

| Stage | Slugs | Required output acceptance |
| --- | --- | --- |
| File trials first | `images_to_pdf`, `pdf_tools`, `text_to_word_pdf`, `cv_formatting`, `csv_review` | Ordered pages/selection; editable Word and matching PDF; actual supplied CV facts/contact; unchanged CSV IDs/zeros/blanks/formula-looking text. Open the real results on mobile. |
| Document/data trials | `document_image_enhancement`, `pdf_tables_excel`, `text_to_office`, `text_to_pdf` | Compare enhanced image with source, no general OCR guarantee; literal PDF cells and source sheets; direct Word/PDF preserves supplied text. Office/PDF smart modes and Excel planning need configured AI and semantic review. |
| Provider-assisted trials | `image_to_text`, `text_translation`, `text_editing`, `text_summary`, `meeting_minutes`, `text_to_pptx`, `pdf_to_word` | Configured provider/rates/budgets, representative AR/EN and numeric tests. Check original OCR text, translation meaning, unchanged facts/negation, important omitted context, actual decisions/assignees, slide readability and PDF extraction limits. |
| Do not add as duplicate | `local_ocr` | Retained historical engine; canonical customer service is `image_to_text`. |
| Internal verification only | `echo` | Test utility, not a distinctive paid deliverable. |

Unconditional AI services require configured provider activation to enable. Mixed
services can be enabled for direct paths, but AI-dependent selections still enforce
runtime provider/budget gates. File engines must be present in the deployed worker;
enabling the database flag alone does not install native programs.

## Development priorities after these trials

1. Fix observed output/UX defects in current services, with source-bound fixtures.
2. Qualify proofreading, key-point extraction and meeting minutes on real AR/EN
   inputs before advertising them as reliable semantic services.
3. Define a separate CV writing/translation contract preserving actual supplied
   career facts and customer review; existing CV service is formatting only.
4. Define source-bound study revision and business document contracts before
   implementing them. They are proposals, not enabled services or hidden flags.

Do not add engine-selection questions to customer menus. Future plugins inherit
generic completion navigation without bot/core service-specific branches.
