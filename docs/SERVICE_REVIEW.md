# Service execution review — 2026-10-23

Owner direction: simplify customer intake, use AI where the task needs it, retain
native file/data operations and verify actual outputs before commercial readiness.
Live source baseline: `267803ac3e188f62580536fe142de7b74e5e32fa`.

## Routing and customer choices

Named standard Word designs use a 24-point title ceiling and 20-point runs for
titles longer than 30 characters, including explicit complex-script sizing.
This is a presentation rule, not a one-line-fit guarantee. It preserves the full
reviewed text, tables, explicit page breaks and resume-specific typography.
Unthemed and literal exports retain their existing behavior. No additional AI
call or service-version change is involved; generated captions remain intact.

The v7 rendering correction removes an opening section title/heading duplicating
the main title only when a single exact source title line confirms the redundancy.
It preserves protected numeric/contact titles, repeated/later source headings,
page-break intent and heading-only bodies. The reviewed plan remains unchanged;
this native display correction adds no AI calls and keeps the v7 schema/version.
Roll out the worker image while preserving provider admission settings.

PDF-to-Word v7 additionally permits native editable Word tables using the existing
bounded Word builder (6 columns, 100 rows/table, 10 tables/document). AI reconstructs
only clear supplied headings/rows and keeps ambiguous or larger extracted content
as complete prose. Numeric/contact occurrence checks cover all visible cells and
captions as well as prose; they do not prove semantic associations or original PDF
layout. Image/form rejection remains unchanged. The isolated `pdf_word` acceptance
case now checks the exact native cell matrix, including row/column associations,
leading zeros and decimal spelling, rather than accepting the same values in
bullets. Run that case on the matching worker before accepting live provider quality.
No extra provider calls or live acceptance cases are introduced. Drain active work
and update API/bot/worker together for this version change, preserving all existing
administrator settings and the intended provider admission state.

| Customer outcome | Execution / AI role | Choices retained |
| --- | --- | --- |
| CSV review | Native parsing, cleanup and audit; no provider call | Requested cleanup/result options |
| CV | Source-bound AI organization/review; native editable Word/PDF | Source details, document language |
| Document image improvement | Native enhancement; AI quality/fidelity review | Source image |
| Image to text | OCR/extraction with AI fidelity review; plain text/export builders | Source images |
| Images to PDF | Native image/page layout; no provider call | Page orientation/order |
| Meeting minutes | AI structure and source evidence; native Word/PDF | Supplied meeting content/options |
| PDF tables to Excel | Native extraction; AI only for proposed column labels | Generic/source/proposed headers, language |
| PDF to Word | Extraction plus source-bound AI reconstruction/review | Source PDF |
| PDF tools | Native extract/merge/rotate; no provider call | Operation, file/page order, rotation |
| Text editing | AI proofreading/rewriting with source checks | Meaningful tone/task choices |
| Summary | AI compression with bounded source references | Language and length |
| Word or Excel | Automatic smart document/source-dataset organization | Word/Excel and content |
| Text to PDF | Automatic smart organization; native rendering | Content |
| PowerPoint | AI source-bound slide plan/review; native PPTX | Content, optional slide count |
| Word/PDF document | Automatic source-bound improvement; native paired output | Output format, optional title |
| Translation | AI translation and source-fidelity review | Target language/style |

The document engine choice is no longer a new intake question. New document
requests improve automatically. A complete first-line `Keep text unchanged` or
`بدون تعديل النص` directive explicitly requests a literal native export; it is
removed from the exported body. Embedded/partial phrases do not change routing.
Explicit old `mode` payloads and saved pre-upgrade schemas retain their validation
and positions. No failed AI result silently falls back to a different deliverable.
AI admission and worker runtime use the same pure `needs_ai(inputs)` contract.
Native operations do not instantiate the provider or create cost holds.

This routing selects a bounded implementation for the requested outcome; it is
not an AI intent classifier and does not claim to infer every possible intention
from arbitrary prose. Supplied-content document services retain source-fidelity
rules. Generating an unsupported factual report from a topic alone is not certified.

## Failure handling and privacy

The observed Word and PPTX requests failed with `provider_invalid`; both released
their test-credit reservations once. Returned usage was settled and under the
declared output/cost bounds. Historical records do not retain the rejected content
or validation/verdict category, so their exact rejection reason is UNKNOWN.

A validated `missing_information=true` now stops with `needs_information` after
one settled call, before any quality-review/correction loop or file delivery.
Schema and quality rejection events are distinct and contain only job reference,
allowlisted validation categories or the validated fixed issue enum. Customer
source, candidate, clarification, raw errors, credentials and provider bodies are
never logged. There is still one bounded creation repair, not autonomous retries.

## Evidence and limits

The previously uploaded full acceptance report contains 29 PASS cases across the
16 services. Later focused reports contain PPTX PASS; five of six strengthened
language/document cases passed, with summary initially failing and then passing
in a separate focused report. These are historical synthetic live-provider runs,
not qualification of this new source or arbitrary customer requests.

Current local and hosted checks are recorded in the PR. Hosted CI must include
the full PostgreSQL/Redis suite, native Office/OCR worker qualification, automatic
intake, old draft compatibility, financial release and cached delivery checks.

The existing 29-case live acceptance plan now exercises automatic defaults for
smart Word, PDF and Word/PDF, without an explicit mode input. It retains bounded
synthetic source content, isolated DB/storage, existing cost caps and no actual
Telegram/Stars charge. Run it after deploying the matching worker and inspect
every delivered artifact. A successful scripted run does not certify visual,
semantic, mobile or invoice correctness, or guarantee 100% provider availability.

## Rollout

No migration, dependency, price, enablement or payment-policy change. Rebuild API,
bot and worker together. Service versions: Word/Excel 9, PDF 6, Word/PDF 4. Verify
no active orders before replacing version-sensitive workers. Registry sync ignores
only `legacy_only=false` as a no-op default for unchanged services, while retaining
all real schema differences and administrator-owned prices/enabled flags.
Use `docs/OPERATIONS.md` and `scripts/service-acceptance.sh`; the isolated live
wrapper requires production AI admission paused first. Preserve and explicitly
restore the intended admission state after reviewing the test results.
