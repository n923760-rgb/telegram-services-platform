# Service portfolio and value gates

Owner-approved expansion, 2026-10-09. The registry is runtime truth; this document
is a staged product roadmap. SAR prices remain administrator-issued test credits.
Commercial digital sales inside Telegram need the separate Stars design already
required by project governance. No production activation is implied by source merge.

Owner continuation, 2026-10-13, authorizes developing/enabling all 16 current public
services through the audited runtime portfolio command in [activation](SERVICE_ACTIVATION.md).
The private verification utility and retired OCR product are excluded. Configuration
preflight, tested source and live output acceptance are separate evidence; future
portfolio candidates below remain unimplemented until their contracts are delivered.

## Integrated source capabilities

| Capability | Customer deliverable and quality boundary |
| --- | --- |
| Word/Excel planning | v8 asks file type first, then requires an explicit Word choice (preserve text / improve wording and organization) before content. Excel skips that question. Legacy internal first-line directive parsing remains; explicit choices treat every line as content. v7 added complete visible smart Word numeric/contact occurrence checks before rendering and on continuation. Excel rows have ordered source IDs and exact cell quotes with conservative number/date/percent/boolean conversions. Native Data references and all nonempty source lines in Source, with retained numeric precision and explicit context counts. One record per source line, <=200 lines/4000 characters each within 12000 total; no formulas/totals. Word modes retained. Context/column/unit meaning and live native/mobile acceptance remain necessary. |
| PowerPoint planning | v7 permits each exact numeric source literal one additional contextual use on a different slide, with the original per-slide count budget and original whole-deck contact budget. Further repetition/new/altered values reject; semantic review still checks meaning, coverage, duplicate records and padding. Prepared v6 files replay; unprepared old work cancels/releases. v6 Arabic/contact direction, v5 optional explicit 1–30 slide count and v4 measured editable layouts retained. Exact slide count is rechecked on continuation. Existing single creation repair, prices and activation retained. Real provider/source meaning/mobile review remains necessary. |
| Text PDF | v4 preserves complete visible AI-plan numeric/contact occurrence counts before rendering and on continuation; direct final text remains provider-free. Meaning/names/live layout still require acceptance. |
| Text PDF to Word | v5 rejects form/permission declarations and orphan widgets before conversion, asking for a static text-based copy. v4 editable extracted text; exact numeric/contact occurrence checks with bounded AI repair/review. These do not prove meaning or names. No original layout/images/table reconstruction promise; updated live acceptance still required. |
| Image text extraction | v6 preserves internal whitespace across long Word-export chunks, matching the retained TXT source after outer trim. v5 is one customer service: received source detail retained, mixed native recognition with configured-AI source review and bounded fallback within the confirmed price. Original text only; optional independent translation after delivery. No engine/language/style questions during extraction. Real photo/provider acceptance remains separate. |
| Independent text translation | Arabic/English target and formal/business/academic/casual style. v2 checks source-line IDs exactly once and preserves numeric/email/HTTP(S)/www URL tokens and occurrence counts per line, rejecting changed, missing, added or moved tokens through the existing single repair. Original blank lines retained; chat text plus UTF-8 TXT. Prepared v1 output remains replayable; unprepared v1 work cancels/releases under the existing version policy. Token matching does not prove translated meaning or recognize every contact notation. Default disabled pending live meaning/style qualification. |
| Independent proofreading/rewriting | Arabic/English original language, proofreading only or formal/business/casual rewriting. v2 retains per-line numeric/email/URL checks, source coverage/order/blank lines and clean edited text plus revision.txt. A deterministic changes.txt shows differing physical lines with exact before/after pairs, no-change disclosure and the complete normalized original for context; no extra AI calls. Historical one-file results remain replayable. Structural validation does not prove semantic fidelity. Default disabled. |
| PDF tables to Excel | Default-disabled v4 `pdf_tables_excel`: bounded image-free text PDFs, internal lattice/stream selection, literal cells and source sheets. Generic, explicit first-row source headings or proposed headings and optional visual-order Arabic recovery are explicit choices; first-row mode moves R1 into Data headers, keeps all original rows in Source and retains R2+ references. Headers must fit the complete review and be unique, nonblank, single-line, at most 100 characters and without edge whitespace; mandatory confirmation. Recovery affects only simple Arabic presentation-form cells in Data; mixed text stays unchanged and Source remains exact extraction. Camelot metrics are heuristics; representative PDF/mobile Excel acceptance required. |
| Text summarization | Default-disabled `text_summary` v3: concise generated points in selected AR/EN language, up to 3/7 points. Single paragraphs accepted. Known source IDs and cited-source numeric/contact token bounds; production AI creation/review/one repair checks decisions, negations, owners and deadlines. Numbered point references appear in chat and TXT; the complete normalized source remains in TXT. These checks do not prove semantic correctness; representative live-provider acceptance remains required. Administrator activation/prices retained. |
| Historical local OCR | Retired as a customer product, retained for historical execution. Its engine is integrated into the single image text extraction service. |
| PDF tools | v3 adds an optional complete file-order permutation for merging, with Arabic/Western/Persian digits and localized previews; skip keeps upload order. v2 merges ordered PDFs, extracts selected pages or applies an explicit additional clockwise 90/180/270-degree rotation to selected pages. Rotation retains every original page in source order, including unselected pages; native content, images and page boxes are retained. No AI; existing file/page limits and form/signature rejection remain. Prepared v1 results replay unchanged. Native/mobile acceptance remains separate. |
| Word/PDF document | v3 asks for Word, PDF or both at the existing service price; only selected artifacts are saved/delivered and the review names the format. v2 literal text by default or explicit AI improvement of wording, grouping and three named native designs. Smart input is bounded to 9000 characters / 80 nonempty lines / 4000 per line, with complete ordered source IDs and per-ID numeric/contact checks. Editable DOCX plus matching native PDF; live meaning/name/layout acceptance remains necessary. |
| Professional CV | v7 single career intake; AI edits/translates into Arabic, English or both in one Word/PDF pair. Request-specific JSON schemas expose exact source IDs, section names/counts, target languages and required/null summary contract. Numeric/contact and semantic guards retained, with bounded AI content review/repair. Model selects three source-owned designs, density, section order and native lead/bullet formatting. Resume-only rendering uses a restrained name/header scale, muted contacts and section accents, lighter long qualification lines and plain skills/languages; other Word layouts retain their design. Bilingual bodies are complete, with English on a fresh page. Education required; experience optional; names/facts/meaning/translation and live provider quality still need acceptance. |
| Meeting-note organization | v4 makes the title optional and uses a neutral localized fallback without an extra AI call. v3 quotes source categories, preserves common dotted names, tracks same-note owners/deadlines and displays the complete review before Word/PDF. Unknowns remain explicit; live AI semantic accuracy remains unqualified. |
| CSV organization/review | v3 adds a Columns sheet for all original columns: original/Data headings, nonempty/empty cells, distinct nonempty literal values and edge-trimmed cells, after the selected whitespace rule. Static case-sensitive counts include duplicate records and exclude generated record references; no missing-value-word/type inference. Preserves sortable Data, Source, row-level Review and optional <=200-record lexical Similarities with disclosed pair cap/numeric exclusions. No row deletion/merging or same-entity confidence claim. Prepared v2 workbooks replay unchanged. |
| Document image contrast | v3 retains received bytes, prepares contrast/sharpen candidates and uses configured AI source review to select a useful candidate; no reliable improvement stops delivery. Selected PNG and comparison, without missing-text reconstruction, deskew or general OCR guarantee. Live visual acceptance remains separate. |
| Images to PDF | v3 adds optional explicit image-page order, validated as a complete permutation before processing; skip keeps upload order. Bounded A4 fit/orientation and received-pixel preservation remain. |

## Current review and development order

Shared file reliability: failed writes/renames now attempt to remove temporary bytes
under the existing owner quota lock, preserving the original exception. Existing
age-based retention remains the fallback if cleanup itself is unavailable. This
applies to uploaded sources and generated artifacts across the portfolio; it does
not make multiple artifact saves transactional or guarantee recovery after SIGKILL.

The complete 16-service contract/UX/quality review and ordered work plan is in
[the 2026-10-16 portfolio review](../ENGINEERING/REPORTS/2026-10-16-service-portfolio-review.md).
Keep the six populated registry categories. Consolidating overlapping Word/PDF entry
points is proposed work, not an already shipped service merge or a price change.

| Current source policy | Services | Operational meaning |
| --- | --- | --- |
| Required AI | 9 | Requires configured, unpaused provider and actual admission checks. |
| Conditional AI | 4 | Office, Text PDF, Word/PDF and PDF-table headings; direct paths remain usable when AI is paused. Office Excel uses AI. |
| No AI | 3 | CSV review, images to PDF and PDF merge/extraction/rotation. |

`optional_ai` is presentation metadata; `needs_ai(inputs)` remains execution authority.
Default-disabled declarations describe installation defaults, not the current database.
Administrator prices/activation and deployed versions require runtime inspection.

Latest operator CV v7 isolated result: Arabic and English PASS, bilingual FAIL with
provider_usage; production pause retained, no active test orders or reserved credit.
The new archive has not been inspected. Prior v6 English output review and older
all-service acceptance do not establish v7 bilingual quality. Next: diagnose that
report with the explicit provider mode now merged; Word mode is explicit in v8. Next unify document entry points safely, then richer
CV/PPTX/Excel, image/PDF and text semantic acceptance. No new inventory is needed
before these improvements.

## Suggested next paid deliverables

These are proposals, not implemented or activated services. Start each with a bounded
source contract, editable/useful output and live customer/provider quality acceptance.

| Service | Concrete customer result |
| --- | --- |
| Summaries/revision extension | Extractive key-point selection is implemented separately. Rewritten summaries and study questions/answers with source references remain proposals requiring new factual/context acceptance. |
| CV further quality qualification | Test representative real Arabic/English/bilingual responses, factual rewrites, transliteration and native/mobile document appearance. |
| Business documents | A quotation/proposal/report from supplied details; no invented tax, legal or financial facts. |

Existing PDF utilities, CSV review, images PDF and direct document bundles
provide deliverables without new AI calls; improve their real acceptance and
pricing before expanding the tool inventory for its own sake. Added source code is
distinct from runtime deployment, service enablement and a qualified paid launch.

## Merge and activation gates

Each bounded plugin has a clear required input/result and honest omissions. Reuse
registered generic intake, abstract providers and existing financial policy; default
disabled. Test invalid inputs before reservation, source numbers/content, structural
files, failure release, cached delivery retry, ownership and retention. Inspect native
sample pages rather than trusting extraction alone. Require exact-head hosted CI and
actual worker qualification, then representative user/provider/staging acceptance
before operator enablement. A library installed or a passing mock does not establish
customer value. Keep all progress in ENGINEERING/MASTER_ROADMAP.md and linked reports.

## Integrated service experience — 2026-10-20

Customers choose deliverables and meaningful content outcomes, not an AI engine
or a separate AI add-on. Required-AI services already select their internal
provider through the shared runtime. Mixed services select their implementation
from the customer's requested outcome through `needs_ai(inputs)`.
Document choices describe preserving the supplied wording versus improving its
wording/organization/design. Preserve-text consent remains explicit; removing an
engine label must not silently authorize rewriting. Format, language, table
heading policy and slide-count choices remain useful output controls.
AR/EN buttons and document previews describe these outcomes without engine labels.
Internal metadata, provider controls and billing safeguards remain operational.

Operator-reported isolated acceptance on 2026-10-20 completed 26/29 cases across
16 services: `word_smart` and `pptx` failed with `provider_invalid`, and
`text_pdf_smart` with `needs_information`. Active test orders and reserved test
credit ended at zero; production provider remained paused. The results archive
has not been reviewed here. Those failures still require diagnosis and a targeted
live rerun; this presentation change does not establish production readiness.

## Selective AI improvement authority — 2026-10-14

The owner authorizes later AI use in existing services when it improves the actual
customer deliverable, while retaining direct tools where sufficient. Do not blanket-enable
AI or alter unrelated plugin contracts in the CV round. Reuse generic `needs_ai(inputs)`,
job-scoped cost holds, content review/one repair and cached delivery. Each follow-up
needs its own source/content and native visual acceptance, bounded price exposure and
versioned tests. AI content review does not inspect rendered page appearance.
