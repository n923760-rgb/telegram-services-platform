# PDF to Word source token fidelity

## Authority and baseline

Owner accepted the review recommendation to strengthen PDF-to-Word content fidelity.
Baseline main 914df9d / PR #67. This round is a bounded service improvement, not a
new payment, table reconstruction or production configuration change.

## Change

PDF-to-Word v4 uses a request-local schema that compares complete multisets of
numeric and email/URL tokens against extracted page content. Title, headings,
paragraphs and bullets all count. Changes, additions, omissions and duplicated
occurrences fail validation. Printable-text checks prevent stripping control
characters from silently changing validated values during DOCX creation.

Synthetic `[Page N]` navigation markers are excluded from the source evidence;
real numeric footers remain source content and must be retained. Customer values
are not embedded in JSON Schema, error messages or operational reports. Injected
provider results are validated again before any builder/storage write.

The existing AI gateway owns the one bounded repair and production content review.
No new provider call/retry loop is introduced by the service. A final invalid plan
fails without an output artifact; normal settlement releases test credit. Provider
usage, including invalid attempts, remains accounted by the existing gateway.

## Compatibility

Unprepared v3 jobs use the existing version-mismatch cancellation/settlement policy.
Prepared artifacts remain replayable without new AI work. Registry synchronization
retains administrator SAR/Stars prices and activation overrides. Input fields,
default gate, financial policy, provider settings and database schema are unchanged.

## Verification

- PASS: 46 focused schema/plugin/Arabic-extraction/architecture cases locally.
- PASS: lint, formatting and whitespace checks.
- Added hosted lifecycle cases for repair/final rejection with production content
  review both off/on, usage accounting, single capture/release, file cleanup,
  retained administrator prices and prepared historical artifact replay.
- The Arabic extraction fixture keeps its original numeric assertions and now
  provides a source-faithful candidate, including the real numeric page footer.
- Full PostgreSQL/Redis/native hosted qualification required before merge.

## Limits

Token equality is not evidence that numbers belong to the right person or sentence;
one negative fixture deliberately documents that limitation. Names, negation,
prose coverage, reading order and semantic correctness still need production AI
review and representative real-provider acceptance. This service remains a text
conversion, not original PDF layout/image/editable-table reconstruction. Source
extraction quality, strict rejection rate and provider cost/latency need live trials.

No production deployment, new activation or real-provider acceptance is claimed.
