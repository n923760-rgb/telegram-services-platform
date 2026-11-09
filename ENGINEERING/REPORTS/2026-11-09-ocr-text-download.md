# OCR literal text download

- FACT: a live mixed Arabic/English screenshot preserved identifiers, dates and negation, but substituted ر.س for the visible currency glyph. Plain text was visible in the source and correctly retained.
- CHANGE: v7 attaches result.txt for short results too, encoded as UTF-8 from the same returned text. Long results retain TXT and editable DOCX with existing render-first cleanup behavior. No extra provider calls.
- CHANGE: strengthen existing verbatim instructions with explicit currency glyph/word examples and visible interface label retention. This is prompt guidance, not independent verification against the image.
- PASS locally: 39 long/short output, cleanup and source-evidence tests; lint and format. Native/AI stubs establish literal export fidelity, not real symbol recognition.
- PENDING: hosted DB-backed upgrade/cache-delivery tests (including v6), full CI, rebuilt-worker/provider acceptance with original currency image. No production change.
