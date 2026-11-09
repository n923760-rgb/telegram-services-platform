# OCR literal text download

- FACT: a live mixed Arabic/English screenshot preserved identifiers, dates and negation, but substituted ر.س for the visible currency glyph. Plain text was visible in the source and correctly retained.
- CHANGE: v7 attaches result.txt for short results too, encoded as UTF-8 from the same returned text. Long results retain TXT and editable DOCX with existing render-first cleanup behavior. No extra provider calls.
- CHANGE: strengthen existing verbatim instructions with explicit currency glyph/word examples and visible interface label retention. This is prompt guidance, not independent verification against the image.
- PASS locally: 39 long/short output, cleanup and source-evidence tests; lint and format. Native/AI stubs establish literal export fidelity, not real symbol recognition.
- PENDING: hosted DB-backed upgrade/cache-delivery tests (including v6), full CI, rebuilt-worker/provider acceptance with original currency image. No production change.

- HOSTED FAIL: run 42559243582 completed with 4130 passed and two stale OCR-version assertions in admin refresh and follow-up intake tests. Updated their expected v7 values; preserve all pricing/flags/draft/ledger assertions.
- INTEGRATION: prepare the corrected OCR tree on main c9097d8 after Word/PDF v5 merge, so the next hosted run verifies both changes together.
- PASS LOCALLY: reran 39 OCR output/cleanup/source-evidence tests and lint/format. DB-backed admin refresh, follow-up suite and complete CI remain pending; PostgreSQL is unavailable locally.
