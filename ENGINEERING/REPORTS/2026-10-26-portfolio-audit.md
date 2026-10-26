# Portfolio audit and expansion boundaries

Source baseline: main `27e5a7a26e1eb428b7cbe9e6ae53e0657c253a0d`.
Owner requests all 16 services reviewed in one round and useful new services,
including Saudi electronic invoicing. This review does not certify paid launch.

## Automated review

One combined local invocation of every public service test_service.py completed:
426 passed in 38.52 seconds, no skips. Synthetic/mocked providers; native Office
fixtures use the bundled soffice via LOCAL_WORD_PDF_TEST_BINARY. No production
DB, Telegram customer or live provider was used. Full hosted baseline evidence:
PR169 workflow 40246230586 passed 3529 tests and 38 network-disabled worker checks.

| Plugin | Baseline tests | Result |
| --- | ---: | --- |
| `images_to_pdf` | 28 | PASS |
| `pdf_tools` | 24 | PASS |
| `pdf_to_word` | 13 | PASS |
| `image_to_text` | 1 | PASS |
| `document_image_enhancement` | 16 | PASS |
| `csv_review` | 31 | PASS |
| `pdf_tables_excel` | 26 | PASS |
| `text_to_office` | 36 | PASS |
| `text_to_word_pdf` | 13 | PASS |
| `text_to_pdf` | 7 | PASS |
| `text_to_pptx` | 44 | PASS |
| `cv_formatting` | 75 | PASS |
| `meeting_minutes` | 20 | PASS |
| `text_editing` | 33 | PASS |
| `text_summary` | 35 | PASS |
| `text_translation` | 24 | PASS |

## Targeted source review

- Input contracts: bounded schemas and needs_ai select native/mixed/AI paths;
  generated menus retain optional fields and no new quality-mode choice.
- Source fidelity: text editing/summary/translation validate numeric/contact/source
  references; semantic negation and quality still need real-provider review.
- Documents: Office/PDF/PPTX revalidate structured plans; CV and minutes reuse
  paired-output preparation. Long/mixed fixtures do not prove target mobile apps.
- Tables: preserve literal values/source references, and review prepared proposals;
  forms/layers are rejected rather than silently losing visible values.
- Images/PDF: ownership, bounded inputs, page/order/rotation and supported-content
  constraints remain in their service/provider boundaries. OCR uses local candidate
  plus provider review and refuses unclear results; image enhancement can legitimately
  return enhancement_not_improved instead of charging for an asserted improvement.
- Failure cleanup: OCR/shared Office/text editing already retain original save errors
  and attempt cleanup. Enhancement lacked that protection: one deletion failure
  could mask the original save/cancellation and prevent remaining cleanup attempts.
  This round fixes that path and adds two failure/cancellation regression cases.
  Successful output/version, price, gate, provider and wallet behavior are unchanged.

## Operator artifacts reviewed

- f7551c4 bundle: seven native cases across five services PASS, zero AI calls/cost,
  no active test orders or reserved funds. Bilingual Word/PDF has all 12 sections;
  PDF extraction/rotation/merge order and source identifiers checked visually.
- 27e5a7a bundle: csv/tables_direct/word_direct/text_pdf_direct all PASS. Hashes match
  report; numeric IDs and literal formula-like text retained. Actual print rendering
  confirms CSV Columns on one horizontal page and PDF-table Review on one page.
  Direct Word/PDF samples contain only three lines and are not long-report evidence.
- Both bundles are synthetic test evidence; checkout SHA is not itself image proof.
  Operator rebuilt the worker for the second run; running production containers were
  not replaced by that command. Production pause remained false.

## Remaining release gates

Run the complete 29-case acceptance matrix in ONE fresh isolated live-provider run,
then inspect every result against its source. Current-run NOT_RUN is not a service
failure or an aggregate historical result. Existing wrapper requires production
PROVIDER_PAUSED=true for live acceptance; native mode cannot run AI cases. No live
run was performed here, and production pause was not changed in this round.

Outstanding: real OCR (English/mixed), enhancement evidence, PDF-to-Word, smart
Office/PDF, PowerPoint, all CV languages, both minutes languages, editing, summary,
translation and AI table labels. Keep semantic correctness, mobile edit/save/reopen
and known Word/Calc numeric-leading-email behavior as explicit manual gates.

## Expansion decision

See docs/COMMERCIAL_SERVICES.md. New services are a proposed implementation queue,
not added/enabled customer plugins. Saudi tax invoicing needs persistent merchant
identity, authorized issuance and regulatory records beyond transient artifact
storage. Do not label a PDF/QR generator as a compliant invoicing system.
