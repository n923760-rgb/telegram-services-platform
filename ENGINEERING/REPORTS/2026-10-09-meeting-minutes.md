# Source-bound meeting note organization

Baseline main 30ec14c419a6712200d3d63920d6d42c025a2cd5, PR #29 merged. Reviewed
workflow 37930551954/job 113819902555 passed 571 tests and actual worker image.
Merged-main workflow 37931140860/job 113821860919 also passed 571 tests and
native image checks. No deployment implied.

Owner authorized useful service expansion and continued publication/merge after checks.
Independent meeting_minutes plugin, disabled by default, SAR 5.00 test credit.

## Contract

Final title, Arabic/English heading choice and source notes: up to 12,000 characters,
80 nonempty lines, 1,200 characters per line. Title trimmed by existing strict model;
CRLF normalized and empty lines omitted from note indexing. Otherwise source note
characters are retained; native dates receive existing invisible LTR formatting.

AI returns only strict integer source IDs and one of discussion/decision/action/review.
Every source ID must occur exactly once, with no omissions, unknown IDs, duplicates,
free-text claims or additional assignee/deadline fields. Request-local schema avoids
source content in schema/model globals. Existing job-scoped gateway/budgets permit
one repair, charge actual provider usage and retain uncertain exposure on failure.

Prompt distinguishes explicit approved decisions from proposals and directs uncertain
or mixed notes to review; content is untrusted data. Schema coverage guarantees do
not prove the semantic category is correct. No paraphrasing/translation/factual
invention in output: deterministic builder copies original notes with numbered IDs
under fixed catalog headings, preserving order within each category. All notes
retained, including repeated source text at distinct IDs.

Customer must review proposed grouping before export. Preview shows counts, all source IDs and up
to two shortened notes per category, not every complete source note; cancellation
releases customer credit while incurred provider usage remains recorded. Confirmation
resume revalidates classification and makes no second AI call. Native Word/PDF pair
uses the existing professional renderer/helper. Capture requires both deliveries;
prepared retry and at-least-once external duplicate limitations remain unchanged.

## Verification

- Local execution unavailable during this slice; local unit/native/visual checks
  NOT RUN. Continue with reviewed Git Data source and exact-head hosted verification.
- Added independent request-local/source coverage tests, strict-ID/extra-fact rejection,
  repeated notes, native DOCX source text, input bounds and review-before-render/resume.
- Added hosted AR/EN review/ownership/success/single capture/provider-cost checks,
  one repair/failure release, decline without export, native render failure, cached
  pair delivery retry and pre-reservation input rejection.
- Actual network-disabled non-root worker exports source-bound Arabic/English plans.
  This tests native output without asserting live AI semantic accuracy.
- No dependency/migration/bot/core/ledger/order/job policy changes. Existing generic
  confirmation and gateway contracts reused; prompts/catalogs remain localized.
- Required exact-head hosted lint/format/full DB/Redis/migration/drift/Compose/image
  results retained on task PR before merge, separately from local evidence.
- NOT RUN: Live provider classification quality, representative meetings/customer
  layouts, native Word/mobile/real Telegram/staging/load or production deployment/
  service activation. Default disabled; operator must qualify those before enabling.

Product value is organized source notes plus editable/shareable documents. This is
not transcript/audio recognition, an autonomous task executor or proof that a note
was actually agreed in a real meeting. No assignee/deadline is inferred.

Review improvement: list all source IDs in each category, even though only two short
samples are shown. Added a coverage test for grouped non-sample references. Initial
workflow 37931262367 spent over five minutes in native-package installation before
any source tests; no test/semantic failure has been observed at this point.

Workflow 37932196007/job 113825382885 passed lint, then failed canonical Ruff wrapping
in two new test expressions. Tests/image were not reached. Apply exact diagnostic
diff; no behavior/validation/check weakening. New exact-head verification required.

## Follow-up after local execution recovered

- PASS: Fresh exact published implementation head 27423a9, tree
  98aa86bdd5cf04e68cce642e3d107b4111ec4b88; 73 independent local checks including
  all 19 minute cases and existing services/architecture. Lint/format pass.
- PASS: Actual local LibreOfficeDev 26.8 alpha exported fixed source-bound Arabic
  and English plans. Both one-page PDFs rendered with Poppler and visually inspected:
  clear categories, each source reference, complete 00123/125.50/00017 and dates.
- Local tests use synthetic plans; no live AI classification/semantic acceptance is
  implied. Hosted full DB/Redis/image checks and final run IDs remain recorded on PR.
- Prior local NOT RUN statuses are initial-stage history, superseded only by these
  synthetic unit/native/visual follow-up checks. Real meetings/native Word/mobile/
  Telegram/staging/deployment/activation remain NOT RUN.
