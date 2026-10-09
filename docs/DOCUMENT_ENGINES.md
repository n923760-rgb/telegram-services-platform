# Document engines and adoption sequence

Owner-approved direction, 2026-10-09: professional outputs by default, deterministic
tools and templates for rendering, AI for content understanding when required.
Use the existing registry, typed plans and job-scoped providers. This is the staged
adoption record; an approved candidate is not an installed or qualified feature.

## Implemented first slice

- `docxtpl` 0.20.2 renders a source-owned reusable professional Word template from
  the existing validated Word plan. The template contains title, conditional headings,
  paragraphs and bullets; the existing builder inserts editable tables in source order.
  Native A4 layout, direction, date isolation, repeated table headers and footer are retained.
- Customer text is escaped context, never template source. Cache only immutable empty
  template bytes; each request has a new renderer and opaque table placeholders.
  Literal Word requests retain the existing untemplated builder and no AI calls.
- All four builders validate generated files before returning them to owner-bound
  storage. Office checks bounded ZIP structure, XML parsing and expected main-part root;
  PDF checks strict parsing, nonempty page tree and positive page dimensions.
- This structural gate does not qualify visual layout, source fidelity, native Office
  interoperability, all relationships or spreadsheet formula correctness. No original
  PDF layout reconstruction is promised. Rendered fixtures are developer evidence only.
- No new intake fields, prices, financial policy, service enablement, provider call or
  schema migration. Professional planning still requires the existing AI call; template
  rendering adds none. A failed gate follows the existing generic failure/release path.

## Local printed-text recognition

The merged PDF slice implements merge and selected-page extraction through the
new `pdf_tools` plugin with existing pypdf, without introducing qpdf or AI. It has
bounded multifile intake, preserves page content/order and rejects forms/signatures.
It remains disabled until operator acceptance. This does not qualify the remaining
candidates below or claim production deployment.

The next bounded source slice adds an independent `local_ocr` plugin (disabled by
default), using an injected `DocumentProcessor` and native Tesseract. Select Arabic,
English or mixed source text, without translation or AI fallback. Existing vision OCR
remains available under its existing gate. SAR 2.00 is administrator-issued test credit.

Native packages are installed only in the `document-worker` Docker target; Compose
selects that target for the existing worker. Bot/API/migrations retain the lean image.
Each worker process serializes local OCR with a five-second queue wait. Each native
child has 512 MiB address-space, 20-second CPU and 2 MiB output-file limits, one
OpenMP thread and a 25-second wall timeout. Cancellation/timeout kills and reaps the
process group before removing its private temporary directory. These are process
bounds, not a sandbox or complete worker/container resource quota. Multiple worker
processes have independent slots. Queue pressure uses the existing bounded job retry.

Intake limits: five images, 10 MiB each/20 MiB total, existing decoded-pixel/EXIF
validation and 1024-pixel normalization, maximum 50,000 output characters. Dense
pages, handwriting, tables and layout reconstruction are unqualified. TSV words
retain native line order, with no numeric rewriting; character-weighted confidence
below 0.70 or a numeric word below 0.85 rejects the request. These scores are only
heuristics: a confidently incorrect recognition can pass. The result asks users to
compare text/numbers with the source. Long text includes a UTF-8 TXT download.
No original page structure, translation or Word reconstruction is promised.

Synthetic native fixtures qualify a small printed-text case in Arabic, English and
mixed mode; English fixture compares an identifier with leading zeros, amount and
date exactly. Full CI adds native lifecycle checks and builds/runs the non-root
worker image with network disabled. Representative customer images, real Telegram
staging, throughput and server installation remain separate acceptance gates.

Tesseract upstream: https://github.com/tesseract-ocr/tesseract (Apache-2.0).
Language data upstream: https://github.com/tesseract-ocr/tessdata_fast (Apache-2.0).
Use the distribution's `tesseract-ocr`, `tesseract-ocr-ara`, `tesseract-ocr-eng`
packages; retain their packaged copyright/license notices. No model weights or
upstream implementation are vendored. Package versions come from the base image's
distribution repositories; image-build qualification does not freeze these versions.
See https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html for the native
interface and https://tesseract-ocr.github.io/tessdoc/Installation.html for packages.

## Remaining candidates

| Candidate | Decision and qualification required |
| --- | --- |
| XlsxWriter | Already installed transitively by python-pptx; explicitly declare it only when used for a measured feature. Retain openpyxl for reading/editing and the current working renderer. Compare native charts/formatting with source-preservation and phone Excel acceptance. |
| PptxGenJS | Compare representative editable Arabic layouts before adding a second language/runtime. Current native python-pptx density safeguards remain the baseline. |
| LibreOffice / unoserver | Next conversion/preview slice in an isolated worker, with serialized execution, hard process timeout, resource limits and temporary-file cleanup. Do not put a listener in the bot or expose it publicly. |
| Tesseract | Bounded local provider and printed-image plugin in this source slice. Require representative Arabic/English customer-image acceptance before enablement. No automatic AI fallback. |
| OCRmyPDF | Searchable scanned-PDF service after the isolated conversion/OCR worker exists. Review licenses of the exact installed components and test large/mixed PDFs. |
| qpdf | No extra installation for merge/extract: pypdf serves the new bounded plugin. Consider qpdf only for an unmet operation; preserve generic multifile intake. |
| WeasyPrint | Introduce only for an approved HTML/CSS PDF design unmet by ReportLab. Restrict URL fetching, fonts, input size and execution resources; preserve the tested Arabic/date baseline. |
| pdfplumber | Already a locked development dependency. Promote to runtime only when a specific table-extraction service is implemented and qualified. |
| MarkItDown | Structured source extraction with document-specific fidelity fixtures and explicit omissions; not a reconstruction engine. |
| Docling | Separate resource-limited experimental worker; benchmark memory, duration, Arabic and table fidelity before enabling a customer service. |
| Argos Translate / rembg | Later isolated services. Validate language/model availability, model licensing and actual Arabic/image quality before paid use. |
| Agent skills | Development guidance, not bot-runtime capabilities. Do not copy source-available Office skill code without exact license review. No uncontrolled agent loops or downloaded customer templates. |

Implement each slice on its own branch, lock only used dependencies, add architecture
and lifecycle checks, require exact-head CI and representative output acceptance.
Keep one canonical roadmap in `ENGINEERING/MASTER_ROADMAP.md`. Installation on the
operator's server and service enablement are separate from source integration.

## Dependency attribution

The unchanged `docxtpl` 0.20.2 package is installed through standard Python dependency
management. Upstream: https://github.com/elapouya/python-docx-template.
License: LGPL 2.1 (`LICENSE.txt`, reviewed upstream blob
`19e307187ac8b9abc086be686dc81b0f09523ef1`); preserve package notices and source access
when distributing it. This project does not vendor or modify upstream implementation
or use upstream sample templates. The template source is authored in this repository.
The wheel retains its license; both uv and container requirements are locked.
Do not generalize this review to the other candidate libraries or their models.
