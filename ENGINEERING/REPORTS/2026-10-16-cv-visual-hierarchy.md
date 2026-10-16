# Resume visual hierarchy

Date: 2026-10-16
Baseline: 244aff0c25529ae7c0e798f1b8bcf5cbdf450972 (#86)
Authority: owner requests continued improvement after reviewing the live English CV archive.

## Observed evidence

The operator supplied isolated CV v6 English PASS, three calls, calculated usage SAR .070128, no active test orders or reserved test credit and retained production pause. Uploaded artifact SHA-256 values matched report.json. The report records generation valid, review invalid_json, then repaired review valid/accepted. Three settled holds and no reported output cap breach. One returned usage equals 8192; equality does not prove a cap breach or establish truncation. No invoice verification.

Word and PDF each render one readable page. Source phone, email and dates were retained, and the generated summary reflects supplied career data. Visual review found the centered name disproportionately large and qualification emphasis too heavy. Sparse test data explains some blank space; do not add invented experience to fill a page. This evidence does not qualify all CVs or production deployment.

## Implementation

CV v7 uses the existing resume layout opt-in after generic typography. Restrained 22pt name, 11.5pt subtitle, 11pt section hierarchy, muted contacts and navy accents for modern/editorial (classic stays black). Source text is unchanged. Long lead lines use normal weight; short role/qualification leads remain bold. Header and section keep-with-next and widow control preserve grouping. Skills/languages use plain source-owned paragraphs, avoiding a bullet around a whole delimited line. Every original source segment remains exactly once; no splitting or guessed structure.

No service-specific branching in core policy. Other Word layouts retain their current typography. Existing validated AI editing/translation, single career intake, bilingual fresh English page, semantic checks, price/gates, budgets, cap, dependencies and migrations unchanged. No live AI call was performed here.

## Verification

PASS: 34 pure contract/layout tests including native dense Arabic and English pagination, exact identifier occurrence/contact preservation and page bounds. PASS: all 75 existing CV regressions with native Office exporter available. PASS: repository lint/format/diff. Initial new layout tests accidentally invoked the shared database fixture; fixed them to declare their pure fixture. Initial dense identifiers overlapped existing certificate 00017; changed the fixture range, retaining exact occurrence checks.

Rendered nine theme/language fixtures plus a typography-only rerender of the old short live content: 13 pages, short monolingual one page and bilingual two pages. Reviewed page images for hierarchy, direction and overlap; not new AI generation. Long native tests exercise two-to-four pages and bounds, not arbitrary inputs. Full hosted workflow required before merge; record its result on the PR. New v7 live acceptance, Word mobile/ATS compatibility and production deployment NOT RUN.

## Remaining work

Explicit employer/role/date and qualification fields need a separately source-bound response contract; this round does not infer or split them. Test richer professional/graduate/academic data and actual customer-reviewed translations before broader quality claims. Operational host bind-mount permissions remain corrected by the operator; no private backup/env permissions were changed here.
