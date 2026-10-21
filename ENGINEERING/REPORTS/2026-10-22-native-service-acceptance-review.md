# Native output review and PowerPoint source language — 2026-10-22

## Evidence and scope

Owner uploaded the synthetic acceptance ZIP after reporting 29/29 cases passing across 16 services, 40 provider calls, zero active orders/reserved credit and production provider pause unchanged. Archive SHA-256: `f229aefce2dc8b42222c6fc4894c436c1811a45944b1b04236f6dcc9da571852`.

The ZIP contains 45 deliverables plus report.json. Every deliverable byte length and SHA-256 matches its report entry. The report explicitly describes its PASS as native/live-provider execution, not visual/mobile/semantic/invoice certification. Its source commit is not recorded in the uploaded archive; b05d60b is the last operator-reported deployed source, not independently verified current server state.

Reviewed all 16 original PDF pages, three additionally rendered unpaired DOCX pages, all three PPTX slides and all 12 workbook tabs, plus text outputs and image comparison. Read native OOXML/source records as well as previews. Secondary office exports were used to investigate renderer disagreements; no original attachment was edited. No live provider or production calls were made here.

## Findings by service group

| Group | Observed result | Qualification limit / next action |
| --- | --- | --- |
| CV AR/EN/bilingual | Readable headings, contact/education/experience, complete separate Arabic/English pages, source facts retained in these short fixtures. | Long careers, dense content and actual Office/mobile editing remain unqualified. |
| Word/PDF direct/smart | The three-line source is present; smart output has a meaningful title/sections/table, no observed clipped text on these pages. Payment negation retained. | No proof of long documents, multi-page tables or all templates. |
| PDF-to-Word | Editable text exists; source records/leading zeros/amounts retained as labelled bullets. | Text-only contract; original source table geometry is not reconstructed. Do not advertise layout-preserving conversion. |
| PowerPoint | Three readable editable native slides, but the English source was translated into Arabic without a requested translation. Review accepted it. | **REVIEW_REQUIRED / actual service defect.** Fix language preservation before accepting this result as professional output. Source is the English three-line fixture in app/ops/acceptance_cases.py; native output text is Arabic, independently of preview rendering. |
| CSV / source Excel / PDF-table Excel | Source rows/zeros/references retained, formula-like text remains text, expected sheets exist. | Preview renderer displayed some text IDs without zeros; native data and secondary office export retained them. No evidence for changing those native cells. Proposed PDF headings intentionally retain the source header as a data row under the existing mode. |
| OCR / images-PDF / PDF tools | Mixed/English synthetic OCR matches the fixture; image order, page extraction, merge and selected rotation match source evidence. | Printed synthetic samples do not qualify camera scans, handwriting, faint stamps or complex forms/tables. |
| Document enhancement | Visible paper illumination benefit; original/comparison/output retained. | Synthetic gradient image, not a difficult real document. Keep no-meaningful-improvement rejection. |
| Minutes | Note classification, source IDs, task owner/deadline and native table are visible. | Arabic selection localizes headings; English source notes are retained intentionally. Test longer/ambiguous real-style minutes. |
| Editing / summary / translation | Payment negation and literal identifiers/amounts preserved. Summary references resolve. | Editing input is already correct and both modes return it unchanged; this does not demonstrate actual correction/rewrite quality. Translation to English uses already-English source; not a cross-language acceptance test. Add representative erroneous/long/cross-language fixtures later. |

## PowerPoint correction

Reuse the existing source contract, which already requires source-language text. Detect only clearly single-script Arabic/ASCII-English prose: remove contacts, require at least 20 letters of one script and no other alphabetic script. Mixed, other-script, short and numeric-only input remains subject to semantic review. For a detected source, reject a deck whose opposite Arabic/Latin script dominates across native titles, bullets, headers and cells. Exclude clarification metadata. Expose the language expectation in the response schema and task prompt.

Use fixed content-free `pptx_source_language` diagnostics and the existing single repair envelope. Do not add retries, semantic-certification claims or a general language classifier. This catches the uploaded full-deck translation, not every partial-language or same-script translation error. Actual source meaning/coverage still requires review. Preserve the existing public input/version, prices/activation, saved prepared results, slide count, numeric/contact guards and financial policy.

## Verification

- PASS locally: 140 focused PowerPoint/repair checks, including 22 new language unit/service cases; three architecture gates; global lint/format/diff.
- Before change, cross-language rejection regressions failed. After change, the actual uploaded PPTX reconstructed from its native text/table fields rejects specifically with `pptx_source_language`.
- Scripted AR→EN/EN→AR wrong outputs repair once (three calls including content review), or fail after two invalid generations with no file. Wrong unprepared continuations reject without calls/files. Mixed/short/other-script sources remain allowed; contacts, metadata and table text have dedicated coverage.
- Four PostgreSQL order-flow tests added for capture/release, cost holds, cached execution, notifications and cleanup. NOT RUN locally: PostgreSQL/Docker unavailable; require hosted suite before merge. These are scripted provider orchestration tests, not a fresh real-provider result.
- Pending runtime gate: rebuild the updated worker image and run isolated `pptx` acceptance, then inspect the resulting language and all slides. Source merge alone does not update the operator's running containers.
- Hosted first run `39680325972` on f848f9e: 2893 tests and all 34 native-worker PASS messages, but the worker step/job was cancelled just beyond the configured 15-minute deadline. Do not report a green workflow. Increase only the bounded job deadline to 20 minutes and rerun the unchanged checks; no skipped tests or relaxed assertions.
