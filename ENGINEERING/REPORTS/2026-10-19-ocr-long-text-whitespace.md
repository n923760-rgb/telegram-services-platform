# Long OCR text: preserve internal whitespace in Word

## Baseline and finding

- FACT: Official main `3e6ff341abb56f4e81ce4c5c622b14f54695c882`
  contains PDF merge order (#107); its qualified tree is
  `6e59e94a0791ecebc3a7c1b1bc1cfe481d668b9f`.
- FACT: ImageToText v5 exports TXT and editable Word for text over 3500 characters.
  Word sections are bounded at 12000 characters. The splitter excluded the selected
  space/newline, then stripped all leading whitespace from the remaining text.
- FAIL REPRODUCED: A native DOCX readback test against the original implementation
  lost a source space at the first chunk boundary while TXT retained it. The test
  compares concatenated body paragraph text, excluding the generated heading.

## Bounded change

- ImageToText v6 includes the split delimiter in the preceding chunk and advances
  without trimming the remainder. Internal spaces, blank lines, tabs and indentation
  survive chunk boundaries in supported Word text. Text order and identifiers remain.
- Keep the existing outer trim, 3500-character artifact threshold, 12000-character
  paragraph limit, 50000-character extraction limit, generated heading and native
  editable Word builder. Unbroken text still uses bounded hard splits.
- No new input, translation, AI stage, dependency, price, activation, provider budget,
  database migration, ledger policy or production setting.
- Existing guards cancel/release unprepared older jobs; prepared historical output
  replays unchanged, without regeneration. Administrator SAR/Stars prices are retained.

## Verification

- PASS LOCALLY: 48 focused tests: 29 new native Word/TXT export tests, 3 existing
  image/source-quality tests, and 16 existing follow-up/service tests. The latter
  pure modules run locally with `--noconftest` because PostgreSQL is unavailable;
  the hosted full-suite DB fixture is unchanged.
- New coverage includes Arabic/English, provider and injected-native recognition,
  spaces/tabs/blank lines/nonbreaking spaces across chunk boundaries, whitespace
  spanning whole chunks, Word edit/save/reopen, artifact thresholds and unbroken
  text at 3500/3501/11999/12000/12001/24001/50000 characters.
- PASS LOCALLY: Three architecture gates, global Ruff lint/format, diff whitespace,
  workflow YAML parsing and embedded worker Python compilation.
- Hosted lifecycle tests extend long source exact readback, prepared v5 replay with
  Word regeneration forbidden, single provider call/capture/cost, and v5 pending
  cancellation/release with administrator settings retained.
- Offline non-root worker qualification adds Arabic/English long-text service export
  with injected recognition and actual DOCX/TXT readback; this isolates export fidelity
  from OCR accuracy and does not claim a real long-image recognition result.
- Full exact-head hosted suite, migrations/drift and worker image qualification are
  required before merge; they are not represented as completed local checks.

## Limits and deployment

- NOT RUN: Live Telegram/provider, Microsoft Word/mobile visual acceptance or server
  deployment. Source qualification is not a claim of universal OCR fidelity.
- Word retains its existing XML-safe text handling and newline representation; this
  round does not promise arbitrary control-character retention or original layout.
  Chunk boundaries still introduce Word paragraph structure; TXT remains the plain
  text reference. The existing outer trim is unchanged.
- Owner requests development first and one later production deployment. No server action.
