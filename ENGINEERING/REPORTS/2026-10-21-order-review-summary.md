# Bounded input summary before purchase — 2026-10-21

## Finding and scope

FACT: main `272c511d5c1b00cb7c4496ade0f2aeb398209710` displays service name and payment
terms at confirmation, but not the selected format, content preparation, requested slide
count, title, page/file order or attachment count. The owner's latest review prioritizes
professional service quality and a clear paid journey. This round implements the summary
part of review finding R05; editing earlier fields and early mixed-mode availability remain
separate work. Existing open quality/PDF/acceptance PRs are not included in this branch.

## Behavior

- Render active fields from the persisted generic input schema. Translate declared choices;
  show supplied short titles/orders/counts, received text character counts and upload counts.
- Short `<prompt_key>_review` catalog labels cover customer contracts and historical OCR;
  unknown future labels use a numbered fallback without requiring a service-specific branch.
- Optional omitted fields show their declared skip behavior, or “Not specified” for the
  generic skip. These are input selections, not validation or a generated-output preview.
- Never echo bulk text, contact contents or upload/storage keys. Bound single-line values;
  remove control characters and render confirmation with explicit plain-text parsing.
- Budget the summary in UTF-16 units, retaining complete original price/Stars terms and
  reporting omitted rows. No new buttons, callback identifiers, schema/service versions,
  price, acceptance, provider, settlement, migration or production changes.
- Existing pending-prompt recovery renders the same review and preserves the purchase key.

## Verification and limits

PASS: 73 focused tests covering the new summary, real draft handlers, existing choice
aliases, document-output contracts, content modes and availability helpers. This includes
18 new cases for Arabic/English, both payment modes, maximum Stars terms with emoji,
conditional PDF fields, ordered attachments, unknown/nested schemas, requested slide
count, titles, input immutability and failed-send recovery. No network/provider/DB calls
are needed by these focused tests. Test counts overlap with the broader invocation below.

PASS: all three existing architecture gates invoked directly; global ruff lint/format and
whitespace checks. Locked development dependencies installed without lock changes.

BLOCKED_ENV: a broader invocation additionally selected 37 existing catalog/unified-service
cases whose shared PostgreSQL autouse fixture could not connect to localhost:55432;
73 passed and 37 setup errors. No assertion failures in that invocation. Do not treat the
unexecuted database cases as passed; full hosted verification remains required.

NOT RUN here: actual Telegram delivery, real-provider/Office/mobile output qualification,
paid checkout/refund, server deployment. This input-review change does not certify output
quality, close the complete R05 editing requirement or resolve provider availability.
