# Sequential service review — 2026-10-25

Source: main `04357a5f6f4dbe52458a2a16dae498d10e457fc6`.
Owner requests service-by-service development with merge deferred. No deployment,
price, activation, production data or provider call was performed in this review.

## Local baseline results

Each service's `app/services/<slug>/test_service.py` ran separately using the
existing development dependencies and synthetic/mocked provider responses.
All 426 tests across the 16 public services pass after resolving the local
Office test binary path. No tests were skipped. These are baseline plugin tests,
not the full PostgreSQL/Redis suite, paid-launch approval or live OCR/AI quality.

| Service | Slug | Tests | Local result |
| --- | --- | ---: | --- |
| Images to PDF | `images_to_pdf` | 28 | PASS |
| PDF page tools | `pdf_tools` | 24 | PASS |
| PDF to Word | `pdf_to_word` | 13 | PASS |
| OCR | `image_to_text` | 1 | PASS |
| Document image enhancement | `document_image_enhancement` | 16 | PASS |
| CSV review | `csv_review` | 31 | PASS |
| PDF tables to Excel | `pdf_tables_excel` | 26 | PASS |
| Office documents | `text_to_office` | 36 | PASS |
| Word/PDF bundle | `text_to_word_pdf` | 13 | PASS |
| Text PDF | `text_to_pdf` | 7 | PASS |
| PowerPoint | `text_to_pptx` | 44 | PASS |
| CV formatting | `cv_formatting` | 75 | PASS |
| Meeting minutes | `meeting_minutes` | 20 | PASS |
| Text editing | `text_editing` | 33 | PASS |
| Summary | `text_summary` | 35 | PASS |
| Translation | `text_translation` | 24 | PASS |

CV and minutes initially failed 5 native render cases because the fixture's
`/usr/bin/soffice` default was unavailable locally. Their complete 95-test sets
passed on retry using `LOCAL_WORD_PDF_TEST_BINARY` with the installed bundled
LibreOffice executable. No service source was changed to mask that environment
failure. Arabic/English CV, long CV and bilingual page-boundary cases ran.

A supplementary image/PDF run passed 154 tests spanning images_to_pdf service,
all bounded input permutations, EXIF handling, PDF tools service, rotation and
merge order. This overlaps baseline tests and must not be added to 426 as a
separate disjoint total. The selected builders/services/tests are unchanged from
the source baseline. This does not certify color profiles or every mobile viewer.

## Improvements kept separate

- CSV draft #161 fixes quoted cell newline fidelity. Its exact-head workflow
  40189827116 passed 3458 tests and 37 network-disabled worker checks. Unmerged.
- PDF table draft #162 rejects form values that both native extractors omit;
  local 85 checks pass. Hosted run 40195780474 was pending at this report's
  preparation. Do not infer its result or include its changes in this baseline.
- OCR review reproduced a partial-output leak when Word rendering or saving fails.
  A separate bounded implementation/test branch addresses render-before-save and
  cleanup after a failed second artifact save. Its evidence belongs to that PR.

## Remaining qualification

Provider-mocked tests cannot establish real transcription, grammar, translation,
summary completeness, invented commitments or real source fidelity. Run isolated
representative provider acceptance and inspect source/output for those services.
Office edit/save/reopen in the target Microsoft/mobile applications remains a
separate check. Known literal Word/Calc numeric-email failures stay open.

Continue repairs only for demonstrated gaps; do not force implementation changes
into services whose reviewed cases pass. Keep each problem in its own draft PR.
