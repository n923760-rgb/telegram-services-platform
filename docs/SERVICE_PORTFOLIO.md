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
| PowerPoint planning | v4 dark cover/light text, paper content slides, explicit native table borders and ISO-date LTR display marks within Arabic paragraphs; original date characters, measured layout bounds and editable objects retained. source-bound native/mobile review remains necessary. |
| Text PDF | v4 preserves complete visible AI-plan numeric/contact occurrence counts before rendering and on continuation; direct final text remains provider-free. Meaning/names/live layout still require acceptance. |
| Text PDF to Word | v4 editable extracted text; exact numeric/contact occurrence checks with bounded AI repair/review. These do not prove meaning or names. No original layout/images/table reconstruction promise; updated live acceptance still required. |
| Image text extraction | v5 is one customer service: received source detail retained, mixed native recognition with configured-AI source review and bounded fallback within the confirmed price. Original text only; optional independent translation after delivery. No engine/language/style questions during extraction. Real photo/provider acceptance remains separate. |
| Independent text translation | Arabic/English target and formal/business/academic/casual style. Source-line IDs checked exactly once, numeric tokens checked per line, original blank lines retained; chat text plus UTF-8 TXT. Default disabled pending live meaning/style qualification. |
| Independent proofreading/rewriting | Arabic/English original language, proofreading only or formal/business/casual rewriting. Per-line numeric/email/URL checks, source coverage/order/blank lines, draft text plus TXT. Structural validation does not prove semantic fidelity. Default disabled. |
| PDF tables to Excel | Default-disabled v3 `pdf_tables_excel`: bounded image-free text PDFs, internal lattice/stream selection, literal cells and source sheets. Generic/proposed headings and optional visual-order Arabic recovery are explicit choices; mandatory confirmation. Recovery affects only simple Arabic presentation-form cells in Data; mixed text stays unchanged and Source remains exact extraction. Camelot metrics are heuristics; representative PDF/mobile Excel acceptance required. |
| Text summarization | Default-disabled `text_summary` v2: concise generated points in selected AR/EN language, up to 3/7 points. Single paragraphs accepted. Known source IDs and cited-source numeric/contact token bounds; production AI creation/review/one repair checks decisions, negations, owners and deadlines. Source and point references retained in TXT only. These checks do not prove semantic correctness; representative live-provider acceptance remains required. Administrator activation/prices retained. |
| Historical local OCR | Retired as a customer product, retained for historical execution. Its engine is integrated into the single image text extraction service. |
| PDF tools | Merge ordered PDFs or extract selected pages, without AI; signatures/forms unsupported. |
| Word/PDF document | v3 asks for Word, PDF or both at the existing service price; only selected artifacts are saved/delivered and the review names the format. v2 literal text by default or explicit AI improvement of wording, grouping and three named native designs. Smart input is bounded to 9000 characters / 80 nonempty lines / 4000 per line, with complete ordered source IDs and per-ID numeric/contact checks. Editable DOCX plus matching native PDF; live meaning/name/layout acceptance remains necessary. |
| Professional CV | v7 single career intake; AI edits/translates into Arabic, English or both in one Word/PDF pair. Request-specific JSON schemas expose exact source IDs, section names/counts, target languages and required/null summary contract. Numeric/contact and semantic guards retained, with bounded AI content review/repair. Model selects three source-owned designs, density, section order and native lead/bullet formatting. Resume-only rendering uses a restrained name/header scale, muted contacts and section accents, lighter long qualification lines and plain skills/languages; other Word layouts retain their design. Bilingual bodies are complete, with English on a fresh page. Education required; experience optional; names/facts/meaning/translation and live provider quality still need acceptance. |
| Meeting-note organization | v3 quotes source categories, preserves common dotted names, tracks same-note owners/deadlines and displays the complete review before Word/PDF. Unknowns remain explicit; live AI semantic accuracy remains unqualified. |
| CSV organization/review | Pasted bounded CSV to sortable Excel with original values, stable record references and static blank/duplicate/edge-change audit. v2 adds optional <=200-record lexical candidates with disclosed pair cap and numeric exclusions. No inferred types/totals, row deletion/merging or same-entity confidence claim. |
| Document image contrast | v3 retains received bytes, prepares contrast/sharpen candidates and uses configured AI source review to select a useful candidate; no reliable improvement stops delivery. Selected PNG and comparison, without missing-text reconstruction, deskew or general OCR guarantee. Live visual acceptance remains separate. |
| Images to PDF | Ordered image pages, bounded A4 fit/orientation and received-pixel preservation; PR #29 passed 571 tests and native image checks. |

## Current review and development order

The complete 16-service contract/UX/quality review and ordered work plan is in
[the 2026-10-16 portfolio review](../ENGINEERING/REPORTS/2026-10-16-service-portfolio-review.md).
Keep the six populated registry categories. Consolidating overlapping Word/PDF entry
points is proposed work, not an already shipped service merge or a price change.

| Current source policy | Services | Operational meaning |
| --- | --- | --- |
| Required AI | 9 | Requires configured, unpaused provider and actual admission checks. |
| Conditional AI | 4 | Office, Text PDF, Word/PDF and PDF-table headings; direct paths remain usable when AI is paused. Office Excel uses AI. |
| No AI | 3 | CSV review, images to PDF and PDF merge/extraction. |

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

## Selective AI improvement authority — 2026-10-14

The owner authorizes later AI use in existing services when it improves the actual
customer deliverable, while retaining direct tools where sufficient. Do not blanket-enable
AI or alter unrelated plugin contracts in the CV round. Reuse generic `needs_ai(inputs)`,
job-scoped cost holds, content review/one repair and cached delivery. Each follow-up
needs its own source/content and native visual acceptance, bounded price exposure and
versioned tests. AI content review does not inspect rendered page appearance.
