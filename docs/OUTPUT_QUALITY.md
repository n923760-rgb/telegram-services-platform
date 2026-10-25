# Customer output quality gates

The owner requires professional, editable Office output across the approved services.
This is a release criterion, not a promise that every possible request is supported.
HTTP health and a successful file export do not establish output quality or paid-launch readiness.

Use the [service readiness report and improvement order](SERVICE_READINESS.md) to
track all services and modes, including cases omitted from a selected test run.

## Service-specific acceptance

| Service/output | Native editability and quality gate | Current limitation / remaining proof |
| --- | --- | --- |
| Professional Word | Native headings, paragraphs, lists and tables. Appropriate structure for the actual task, no boilerplate. Reopen, edit, save and compare names, IDs, dates, amounts and material notes with the source. Inspect every page, mixed-language runs and repeated headers. | AI fidelity is not established by schema validation. Representative real-provider and Microsoft Office checks remain required. Literal transfer stays explicit. |
| Excel | One native filterable table with a visible title, frozen headers and editable typed cells. IDs keep zeros, missing cells stay blank, zero stays zero, duplicate records stay present. Dates and percentages are typed only when their meaning is unambiguous. Independently reconcile source records and numerical values. | Single dataset, up to 50 columns/1,000 rows and a bounded plan. No generated formulas, charts, multiple datasets or automatic totals. Very long cells can exceed Excel's row-height limit; inspect the formula bar and enlarge columns. Wide printouts may span pages. |
| PowerPoint | Native titles, bullet paragraphs and editable tables, with bounded font-metric density checks. A dense first slide uses the normal content layout; a single-slide request receives no extra cover. Edit and save text/cells in PowerPoint. Compare all material source facts and inspect every slide for actual overflow. | Tables support 1–4 columns and 1–6 rows per slide. No native charts, images, branding or arbitrary compositions. Font metrics are conservative estimates, not proof of Office rendering. Arabic/mixed-direction rendering and font substitution require Microsoft PowerPoint acceptance. |
| Text to PDF | Readable Arabic/English, correct shaping and page breaks, intact source facts, no cropped content. Numeric dates retain their supplied digit/separator order during RTL rendering and width measurement. Inspect every page in a PDF viewer. | Dates are displayed literally; ambiguous notation and calendar meaning are not interpreted. PDF is fixed-layout; use DOCX/XLSX/PPTX for Office editing. Source fidelity and representative viewer checks remain required. |
| PDF to Word | Editable reconstructed text with conservative headings/lists and source-bound fidelity. Check extracted numbers, dates, reading order and omissions on every source page. Reject declared optional layers before text extraction/AI, and raster image drawing instructions, including inline images and nested Forms, before AI/output. | Text-only conversion: even a displayed logo/image is conservatively rejected because image meaning is unknown. Unused image resources are allowed. Layered PDFs require a reviewed flat export from the original application. This is not OCR, vector/chart/annotation reconstruction, native table reconstruction or a layer editor. AI and reading-order fidelity remain unqualified; do not advertise full-fidelity conversion. |
| PDF tables to Excel | Reject declared optional layers before either native table extraction method or AI labels. Preserve accepted source cell strings and source references in the editable workbook. | Text extractors can read content hidden by layer defaults. Empty/indirect configurations are also unsupported; export a flat text-based PDF from the original application and inspect it before upload. This does not flatten, redact or sanitize arbitrary hidden content. Table extraction and target Office acceptance still require source-by-source review. |
| PDF page tools | Preserve copied page content, images, boxes and requested page/file order. Merge, extract and rotate reject forms/signatures and declared optional-layer configuration before constructing output. | Page copying does not retain catalog layer-visibility defaults and can reveal hidden content. Layered PDFs are unsupported, including empty or indirect declarations and layers on unselected pages. Export and inspect a flattened copy in the original application before upload. This tool does not flatten, redact or edit layers; this is not a general PDF sanitizer. Existing outlines/metadata limitations remain. |
| OCR / translated OCR | Compare extracted/translated text with supplied images, identifiers and reading order. Translation keeps literal numeric tokens and their occurrence counts from extracted text; mismatches enter the existing one repair, then fail. Unreadable input fails honestly. Long DOCX output uses native text. | This numerical check compares translation with model-extracted text, not the image. It cannot verify names, units, associations, complete prose or OCR accuracy. Digit localization, number spelling, date/percentage reformatting and other numeric notation changes are intentionally rejected. Confidence is not source-fidelity proof. |

Do not turn unsupported customer requests into polished but incomplete output and label it successful.
Do not add fabricated signatures, citations, commitments, totals, dates or duplicate copies of records.
If a required capability is missing, clarify the scope before purchase/service enablement.

## Required evidence before claiming qualification

Numeric-leading email addresses inside Arabic prose need specific mixed-direction
acceptance. Word now treats the complete ASCII email as one LTR run before
matching dates, including headings, captions and table cells. Professional date-
formatted exports apply boundaries around that complete token; literal exports
preserve the original characters without adding controls. LibreOffice still
reorders the numeric address in the literal Word fixture, so its run-direction
assertions alone do not qualify that viewer case. Excel uses the same
complete-token detection for Arabic cell alignment while preserving literal cell
values. A synthetic LibreOffice Calc printout still reverses portions of such an
email inside an Arabic cell, both before and after the detection correction.
This remains a failed viewer case, not qualified mixed-cell presentation. Do not
insert display controls into literal XLSX data or infer Microsoft Excel behavior
from that printout. Test the actual target Office app separately. PowerPoint reuses
the same matcher while retaining its existing whole-token direction boundaries.

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

## Word table layout

Native Word tables use the final document margins before allocating column widths.
Measured words, including bold headers, receive space at the existing 10pt cell
font; long identifiers have bounded demand so one contact cannot monopolize the
page. If all requested minima cannot fit, widths share the available space and
text wraps. Local font absence uses an approximate fallback and does not prevent
editable DOCX generation. This is a layout estimate, not target-Office proof.
Wider short-field columns can increase wrapping in narrative columns and page
count; never delete records or shrink cell fonts to hide that tradeoff. Repeated
headers and native editable rows remain required on multipage tables.

## Excel delivery conventions

Print layout uses the final column widths and A4 margins. A sheet that fits uses
one page in width and unlimited pages in height; wider datasets use landscape at
100% scale across horizontal pages rather than shrinking all columns into tiny
text. Wide printouts include Excel row/column headings so corresponding record
positions can be compared across pages. Source exports re-evaluate the layout
after padding/reference widths, and CSV/PDF-table sheet copies retain print options.
Cell values, types, column order, table filters and editing behavior are unchanged.
This can increase printed page counts. Width estimation is approximate; font
substitution, long merged titles and actual Microsoft Excel/mobile printing still
require target-viewer acceptance. Calc can emit clipped merged-title copies beyond
later horizontal panes; native PDF regression checks first-pane title and table
glyphs separately. This is not a general Excel-to-PDF conversion service.

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

## PowerPoint delivery conventions

The deck preserves its validated slide count. A concise first slide in a multi-slide deck may
use a cover layout; otherwise it uses the same content layout as subsequent slides. Native
titles use 32/42 pt, content uses 20–26 pt and table cells use 20/21 pt. Slide-number footers
use 12 pt. Density failures enter the existing single AI repair, then fail honestly if still
invalid. The builder never fixes density by deleting records, adding slides or shrinking body
text below 20 pt. The provider must preserve the requested count and material source facts.
Titles/bullets and tables are alternative bodies; table text preserves identifiers, missing
cells, dates and duplicate rows without interpreting them as formulas. Pending version-1
orders are cancelled and their reservation released after registry synchronization to version 2;
administrator-owned enablement and price remain intact. Already prepared deliveries retain
the existing cached-delivery path.
