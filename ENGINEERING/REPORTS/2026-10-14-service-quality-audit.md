# Public service quality and selective AI review

## Scope and authority

Owner requests review, development and improved quality across all existing services,
with AI where it materially helps and direct tools where adequate. Source baseline:
`995f03a3b70e0a51a98c985daf7bab1a15475edc` (CV v5, PR #76). This is an initial
review of public entry points, AI decisions, schemas, shared financial/review/replay
controls and attributable tests, not a full penetration audit or live quality certification.
Private echo and retired local OCR are excluded from the 16-service customer portfolio.

Last supplied server deployment is `288d044`; deployment of CV v5 is NOT CONFIRMED.
Previous operator evidence showed all 16 enabled, test credit and a paused provider.
Source defaults remain disabled; actual DB-owned gates/prices are not inferred from code.

## Service-by-service source assessment

| Service | AI policy at baseline | Current guard and remaining improvement |
| --- | --- | --- |
| CV v5 | Required | Single intake, editing/translation/design, per-source numeric/contact checks and bounded semantic review. Real provider, transliteration and mobile acceptance outstanding; never certify ATS or employment. |
| Meeting minutes v3 | Required | Source-note IDs, quoted names/owners/deadlines, complete review and Word/PDF. Qualify real classification and final layout; future rewriting must retain source evidence. |
| Image text extraction v5 | Required for public orders | Native recognition then AI source review/fallback; final text is not meant to be rewritten. Test real mixed-language photos, difficult digits, unclear text and provider cost. Native confidence is not a correctness proof. |
| Document image enhancement v3 | Required | Native contrast/sharpen candidates with AI selection and received-source copy. Real images must demonstrate improvement without deleting stamps/details; no missing-text reconstruction. |
| PDF to Word v4 | Required | Text-only PDFs, source numeric/contact occurrence checks and bounded review/repair. Scanned/image PDFs rejected; no original layout/table/image recreation. Real source/provider qualification remains outstanding. |
| Translation v1 | Required | Per-line IDs/numeric fidelity and reviewed translation. Qualify names, negation, tense and domain terminology; not certified translation. |
| Text editing v1 | Required | Per-line numeric/email/URL checks; proofread/rewrite choices. Qualify meaning, commitments and names; keep editing distinct from extraction/translation. |
| Summary v2 | Required | Known cited IDs and numeric/contact limits, retained source report. Evaluate decisions/negations/owners and intentional coverage; reference checks do not prove factual meaning. |
| PowerPoint v2 | Required | Native editable slides/tables and readability bounds, but source control validation occurred after admission and no independent numeric/contact guard existed. Addressed in this round as v3. |
| Word or Excel v5 | Conditional | Direct Word through explicit first-line keep-text directive; AI for professional Word/Excel. Future source-bound Word checks and record-level Excel provenance are priorities. Excel percentage/date normalization needs typed checks, not blind raw-token comparison. |
| Text PDF v3 | Conditional | Direct source text or AI organization. Improve source-grounded smart planning and match its layout quality to the Word/PDF path; literal mode stays available. |
| PDF tables to Excel v3 | Conditional | Native extraction; AI only for proposed labels, with confirmation. Source sheets remain unchanged; real multi-page/merged-cell and Arabic mixed-cell acceptance needed. Do not let AI silently alter values. |
| Word and PDF v1 | Direct | Exact source text and shared native pair/preview/replay. Next feature: explicit content-improvement mode with source-bound AI while preserving literal/default behavior. Not implemented by this safety round. |
| Images to PDF v2 | Direct | Received pixels, order/aspect ratio, bounded native export. Keep direct; enhancement is a separate consented outcome, not a reason to call AI for assembly. |
| PDF merge/extract v1 | Direct | Deterministic page operations. Keep direct; test unusual structures/rotation and reject unsupported signed/forms workflows. AI adds no necessary value here. |
| CSV review v2 | Direct | Literal source sheet, trimming/duplicate/blank audit and bounded lexical candidates. Keep values/formula-like text/IDs exact. Later AI explanation could be a separate reviewed note, never unapproved row deletion or value correction. |

FACT: Nine required-AI, three conditional-AI and four direct services at this baseline.
Added pure policy cases cover every public service and meaningful mixed mode. They do
not probe production configuration, service enablement, provider billing or actual quality.

## Implemented safety improvements

- PowerPoint v3 validates printable input through pure admission before reservation.
  Source-local output schema rejects new/altered/over-repeated numeric/email/URL tokens
  across titles, bullets, column headers and table cells. Continuations and injected
  responses are revalidated before output writes. Cached approval needs no fresh AI.
- Counter inclusion deliberately permits omission of instruction-only slide-count numbers;
  it does NOT prove required content coverage, semantic association, names or meaning.
  Existing bounded semantic review remains required; no claim of lossless numeric coverage.
- Generic input digest rejects non-UTF-8/non-JSON content with a safe input error before
  DB work. Valid hashes remain byte-identical, preserving order/payment idempotency.
  No service branches, ledger rewrites, financial policy, prices, activation, dependency,
  migration, provider-pause or rendering/layout changes.
- Tests use explicit source-containing PPTX fixtures rather than outputs whose numbers
  were absent from a placeholder input. This is mock evidence, not live AI evidence.
- PASS LOCALLY: 91 focused source/service/native-structure/policy/architecture cases,
  lint/format/diff. Full hosted DB/cost/capture/release/replay/concurrency and native-worker
  qualification required before merge. New financial cases verify invalid-source rejection,
  bounded numeric repair/failure, retained billable usage, one settlement and cached approval.

## Ordered next rounds

1. Qualify/deploy the current CV and safety changes; review historical provider exposure
   and corrected request contract before restoring AI. Do not invent or delete unknown cost.
2. Add explicit optional source-bound AI improvement to Word/PDF, retaining literal mode;
   then strengthen smart Word/PDF source checks and final native page review.
3. Strengthen Excel record/numeric provenance and inspect real editable/printed output;
   then qualify PowerPoint and OCR on representative actual inputs.
4. Evaluate translation/summary/editing/minutes against supplied facts, names, negatives,
   dates and accountability; qualify image improvement by visible received-source comparison.
5. Retest direct PDF/image/CSV tools for usability and edge cases without unnecessary AI.

NOT RUN: New production deployment, provider invoice reconciliation, any live AI call,
all-service Telegram/mobile acceptance or universal security/quality certification.
