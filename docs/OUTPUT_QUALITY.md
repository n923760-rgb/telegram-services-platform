# Customer output quality gates

The owner requires professional, editable Office output across the approved services.
This is a release criterion, not a promise that every possible request is supported.
HTTP health and a successful file export do not establish output quality or paid-launch readiness.

## Service-specific acceptance

| Service/output | Native editability and quality gate | Current limitation / remaining proof |
| --- | --- | --- |
| Professional Word | Native headings, paragraphs, lists and tables. Appropriate structure for the actual task, no boilerplate. Reopen, edit, save and compare names, IDs, dates, amounts and material notes with the source. Inspect every page, mixed-language runs and repeated headers. | AI fidelity is not established by schema validation. Representative real-provider and Microsoft Office checks remain required. Literal transfer stays explicit. |
| Excel | One native filterable table with a visible title, frozen headers and editable typed cells. IDs keep zeros, missing cells stay blank, zero stays zero, duplicate records stay present. Dates and percentages are typed only when their meaning is unambiguous. Independently reconcile source records and numerical values. | Single dataset, up to 50 columns/1,000 rows and a bounded plan. No generated formulas, charts, multiple datasets or automatic totals. Very long cells can exceed Excel's row-height limit; inspect the formula bar and enlarge columns. Wide printouts may span pages. |
| PowerPoint | Native text objects, readable hierarchy and intentional slide structure. Edit and save text in PowerPoint. Compare all material source facts. Inspect every slide for actual text overflow, not just bounding-box overlap. | Current plan supports titles and bullets only. Native charts/tables and advanced slide compositions are not implemented. Dense first slides need a separate rendering improvement and qualification. |
| Text to PDF | Readable Arabic/English, correct shaping and page breaks, intact source facts, no cropped content. Inspect every page in a PDF viewer. | PDF is the fixed-layout delivery format, not a promise of Office editability. Use DOCX/XLSX/PPTX for editing. |
| PDF to Word | Editable reconstructed text with conservative headings/lists and source-bound fidelity. Check extracted numbers, dates, reading order and omissions on every source page. | Scanned/mixed PDFs fail honestly; original layout, images and native table reconstruction are outside the current contract. Do not advertise this as full-fidelity conversion. |
| OCR / translated OCR | Compare extracted/translated text with the supplied images, including identifiers and reading order. Unreadable input fails honestly. Long DOCX output uses native text. | Model confidence is not a source-fidelity guarantee. OCR is transcription, not permission to invent or rewrite obscured facts. |

Do not turn unsupported customer requests into polished but incomplete output and label it successful.
Do not add fabricated signatures, citations, commitments, totals, dates or duplicate copies of records.
If a required capability is missing, clarify the scope before purchase/service enablement.

## Required evidence before claiming qualification

Use a dedicated staging customer and synthetic Arabic, English and mixed-language content.
For each service test a typical request and relevant boundaries: short/long content, missing
data, duplicate records, zero, leading-zero IDs and ambiguous dates. For Office outputs:

1. Compare the source with the reopened document/workbook/deck. Check completeness separately
   from structure and appearance. Inspect native objects and reject unintended formulas,
   macros or external references.
2. Render and inspect every page/slide or changed sheet at readable zoom. No clipped text,
   reversed dates, illegible cells or blank terminal pages. Record the rendering engine.
3. Open in the customer's intended Microsoft Office application, change a text/cell/object,
   save and reopen. Record the application/version; XML/reopening tests are not this check.
4. Verify only delivered results capture customer credit once. Rejection/failure releases;
   delivery retry reuses prepared files rather than calling AI again.

Retain source SHA, test case, order ID, sanitized source/output comparison, engine and
PASS/FAIL/NOT RUN. No real customer content or secrets in Git/evidence. A test using a fixed
plan is not a live-provider acceptance result. Deployment, payments and paid launch require
their own approvals; SAR credits remain test credits under current governance.

## Excel delivery conventions

`Data!A1` is the title, row 2 separates it from the dataset, row 3 contains the native `Records`
table headers and data starts at row 4. Users can sort/filter with the header controls and edit
cells normally. Adding records is an intended native Excel Table workflow; verify actual table
expansion in Excel before advertising it as qualified. Existing legacy plans without format
metadata still work; ambiguous dates and mixed columns stay text/mixed rather than being guessed.
Explicit ISO Gregorian dates (1900 onward) become sortable dates. Supplied percentages use
numeric fractions. Numeric plans exceeding Excel's 15-significant-digit precision are rejected;
the provider must preserve such source values as text. No arbitrary format strings or formulas
from the provider are executed. Missing/duplicate counts in the delivery preview are observations,
not corrections, and never delete source records.
