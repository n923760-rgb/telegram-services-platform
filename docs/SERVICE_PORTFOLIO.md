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
| Word/Excel planning | Editable documents/tables from source; native Office/source fidelity acceptance remains necessary. |
| PowerPoint planning | Editable bounded slide layouts; source-bound native/mobile review remains necessary. |
| Text PDF | Direct final text or existing AI planning, with Arabic/date checks. |
| Text PDF to Word | Editable extracted text; no original layout/images/table reconstruction promise. |
| Image text extraction | v5 is one customer service: received source detail retained, mixed native recognition with configured-AI source review and bounded fallback within the confirmed price. Original text only; optional independent translation after delivery. No engine/language/style questions during extraction. Real photo/provider acceptance remains separate. |
| Independent text translation | Arabic/English target and formal/business/academic/casual style. Source-line IDs checked exactly once, numeric tokens checked per line, original blank lines retained; chat text plus UTF-8 TXT. Default disabled pending live meaning/style qualification. |
| Independent proofreading/rewriting | Arabic/English original language, proofreading only or formal/business/casual rewriting. Per-line numeric/email/URL checks, source coverage/order/blank lines, draft text plus TXT. Structural validation does not prove semantic fidelity. Default disabled. |
| PDF tables to Excel | Default-disabled v2 `pdf_tables_excel`: bounded image-free text PDFs, internal lattice/stream selection, literal cells and source sheets. Generic/proposed headings are output choices; mandatory confirmation. Camelot metrics are heuristics; representative PDF/mobile Excel acceptance required. |
| Text summarization | Default-disabled `text_summary` v2: concise generated points in selected AR/EN language, up to 3/7 points. Single paragraphs accepted. Known source IDs and cited-source numeric/contact token bounds; production AI creation/review/one repair checks decisions, negations, owners and deadlines. Source and point references retained in TXT only. These checks do not prove semantic correctness; representative live-provider acceptance remains required. Administrator activation/prices retained. |
| Historical local OCR | Retired as a customer product, retained for historical execution. Its engine is integrated into the single image text extraction service. |
| PDF tools | Merge ordered PDFs or extract selected pages, without AI; signatures/forms unsupported. |
| Word/PDF bundle | Final text, professional template, editable DOCX plus native PDF from the same document. |
| CV formatting | Structured final career facts, Arabic/English headings, classic single-column Word/PDF; PR #28 passed 545 hosted tests and native CV checks. |
| Meeting-note organization | v3 quotes source categories, preserves common dotted names, tracks same-note owners/deadlines and displays the complete review before Word/PDF. Unknowns remain explicit; live AI semantic accuracy remains unqualified. |
| CSV organization/review | Pasted bounded CSV to sortable Excel with original values, stable record references and static blank/duplicate/edge-change audit. v2 adds optional <=200-record lexical candidates with disclosed pair cap and numeric exclusions. No inferred types/totals, row deletion/merging or same-entity confidence claim. |
| Document image contrast | v3 retains received bytes, prepares contrast/sharpen candidates and uses configured AI source review to select a useful candidate; no reliable improvement stops delivery. Selected PNG and comparison, without missing-text reconstruction, deskew or general OCR guarantee. Live visual acceptance remains separate. |
| Images to PDF | Ordered image pages, bounded A4 fit/orientation and received-pixel preservation; PR #29 passed 571 tests and native image checks. |

## Current integration queue

| Priority | Service | Value and acceptance required |
| --- | --- | --- |
| Current | Extract key points | Owner continuation, 2026-10-10. First extractive summary slice: 2–80 nonempty source lines / 12000 characters. Not a comprehensive abstractive summary or study question generator; validate usefulness before paid launch. |
| Merged | Independent proofreading/rewriting | Added after owner continuation, 2026-10-10. Bounded original-language pasted text; customer reviews draft. Real-provider names/negation/claims/style acceptance required. |
| Merged | Independent text translation | Added on owner request, 2026-10-10. Bounded pasted text only; no uploaded-document layout reconstruction, certified translation or claim that structural checks prove semantic accuracy. |
| 1 | CV formatting (merged, disabled) | Structured actual career details, classic single-column Word/PDF, Arabic or English headings. Formatting only; no invented facts, translation or ATS/job outcome guarantee. Native content/layout and capture/release tests required. |
| 2 | Images to PDF (merged, disabled) | Ordered pages, EXIF orientation, consistent A4 layout and original aspect ratio. Quality bounded by uploaded image resolution; no OCR or scan-enhancement promise. |
| 3 | Meeting-note organization (merged, disabled) | Decisions/actions grouped from source notes with traceable references, no invented assignees/deadlines. Requires source-bound extraction/schema repair and real-provider semantic qualification. |
| 4 | CSV organization/review (current slice) | Preserve original IDs, blanks, zero/duplicates; explicit delimiter/edge rules, original sheet, stable record references and audit sheet. No inferred totals/data deletion or executable customer formulas. Native Excel/mobile acceptance required. |
| 5 | CV writing/translation | Evidence-bound rewriting of supplied career facts, with review before delivery. Requires factual/source checks and real Arabic/English provider acceptance beyond formatting. |
| 6 | Study revision pack | Source-bound summary, revision questions and answers with references. Requires omission/fact checks; never fabricate external sources. |
| 7 | Business document packs | Brief/report/proposal from actual supplied facts, consistent Word/PDF. Define each contract and verification before adding a plugin. |
| Later | Searchable scanned PDF, background removal, compression | Qualify resource/model/component licenses and actual output improvement separately before installing tools. |

## Suggested next paid deliverables

These are proposals, not implemented or activated services. Start each with a bounded
source contract, editable/useful output and live customer/provider quality acceptance.

| Service | Concrete customer result |
| --- | --- |
| Summaries/revision extension | Extractive key-point selection is implemented separately. Rewritten summaries and study questions/answers with source references remain proposals requiring new factual/context acceptance. |
| CV writing/translation | Rewrite actual provided career facts, then use the existing CV Word/PDF formatter; no invented achievements. |
| Business documents | A quotation/proposal/report from supplied details; no invented tax, legal or financial facts. |

Existing CV formatting, PDF utilities, CSV review, images PDF and document bundles
already provide deliverables without new AI calls; improve their real acceptance and
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
