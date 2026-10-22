# Original OCR and optional independent translation

Date: 2026-10-11. Baseline main: 79d063e69a2cccdeb9342d6bfba75477bf807ba0.

## Problem and behavior

FACT: AI OCR v2 asked for translation and style before extracting the image text.
Owner requested original extraction followed by optional independent translation.

AI OCR v3 now collects images, shows the existing price confirmation and delivers
original extracted text. Its menu name explicitly mentions AI. Local OCR still asks
for the source language because Tesseract needs it; this is not a translation choice.

Both plugins declare a generic result-text shortcut. After delivery, an eligible
result offers Translate text. This opens existing text_translation intake with the
original text prefilled; the customer chooses target language/style and confirms
that independent request and its live price. Clicking/cancelling does not create
an order or reserve funds. Original order/result is untouched.

## Boundaries and retention

- Plugin-owned declarations, up to three actions; no named service branch in core,
  orders, workers or wallet. Only the first unconditional free-text field may be prefilled.
- The callback contains only source UUID and action index, never customer text.
- Every click rereads ownership, completed status, retained result, source version,
  configured file TTL, target enabled/version/schema/provider/payment eligibility.
  Delivery may offer a shortcut while its source status is delivering; a click is
  accepted only after completion, so very early clicks may need repeating.
- Target source limits are checked without an AI call: 12000 characters, 80 nonblank
  lines and printable text. Ineligible text is never truncated or silently translated.
- Active drafts survive repeated/new result clicks. Prompt failures retain the usual
  pending marker for recovery. The prefilled draft uses existing one-hour Redis TTL;
  no separate source cache or DB migration is introduced.
- Existing delivery remains at least once. A crash/outbound failure can duplicate
  original result messages; this shortcut does not promise exactly-once delivery.
- AI OCR contract version bumped to 3; queued v2 work is rejected/cancelled through
  existing version checks and reservation release, rather than reinterpreted.
  Local OCR input/execution unchanged; no version bump or activation/price reset.
- Existing test-credit/Stars admission and confirmation behavior is reused unchanged.
  Payment completion remains deferred by the owner.

## Verification

PASS LOCAL: 41 focused pure checks (callback bounds, source limits, OCR intake,
shared numeric safeguards, plugin architecture) and reviewed source change.
Full disposable-DB lifecycle, drift, Compose and all native worker gates require
hosted exact-head qualification; PR records actual head/run/test evidence before merge.

First hosted head fd5ed5df00bf5447df0f2f339ac94e03689b0db5 / run 38116559302:
1042 passed, one failed, one warning in 315.83s. Failure was the retained long-output
Word editability assertion: it edited only the first run, but Arabic/date text uses
several direction-aware runs. Corrected to edit the complete paragraph and locally
verified numeric counts plus edit/save/reopen on the actual builder's Arabic output.
This did not change generated files or loosen source-content checks. Drift/Compose/
native steps were skipped on the failed run; the corrected head requires a full rerun.

NOT RUN: VPS update, mobile UX and real AI/Tesseract/translation meaning/style
acceptance for this new path. Existing operator checks do not qualify this change.
