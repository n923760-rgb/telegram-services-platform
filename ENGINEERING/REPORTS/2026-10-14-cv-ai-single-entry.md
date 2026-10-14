# Single-entry AI CV editing translation and design

## Authority and baseline

- OWNER AUTHORITY: Improve the poor CV result; allow AI editing, translation and design;
  enter career data once. Later use AI selectively in existing services where useful.
- FACT: Baseline main `288d0440f23a0590f920391270e9328a9bdb474b`, CV v4.
- SCOPE: One CV feature plus generic opt-in Word rendering support. No new services,
  bot/core service branches, dependencies, migration, price or default gate changes.

## Delivered contract

- CV v5 requires the existing abstract, job-scoped AI. Four purpose profiles retained.
  One 14-field intake; education/name/contact/skills required, experience optional.
  Duplicate English form removed. Customer can enter actual details in either language.
- One bounded editing/translation/design task uses existing automatic semantic review
  and at most one candidate correction; no autonomous iteration or vendor-specific code.
- Each requested language must cover every original segment ID exactly once. Numeric
  tokens, date notation, phone formatting, emails and URLs match per-source occurrence
  counters. Original-script name retained verbatim; other-script transliteration reviewed.
- Every supplied body section remains present once; source line order retained within
  sections. No absent experience/skills/qualifications generated. If summary is skipped,
  a short summary references known career source IDs and cannot add numeric/contact claims.
- Bounds: 9000 source characters, existing individual field limits, 160 nonempty source
  segments; 15000 output characters per language. Provider token/cost bounds unchanged.
- AI chooses modern/classic/editorial typography, comfortable/compact density, section
  order and lead/paragraph/bullet presentation. Builders create editable body text with
  readable 11pt text, named black styles, native bullets and script-aware runs.
- Bilingual output: complete Arabic CV then complete English CV on a fresh page, in ONE
  DOCX and its matching PDF. Not alternating paragraphs; no forced single-page promise.
- Generic Word extension: typed designs, ordered mixed blocks, section alignment and
  titled page breaks. Existing standard defaults retained. Values escaped; no generated
  code, font paths, arbitrary coordinates or externally fetched design assets.
- Existing prepared-result/preview/storage/retention/cost lifecycle reused. Delivery
  retries reuse persisted files, including after partial delivery; no repeat AI charges.

## Evidence and limits

- PASS LOCALLY: 105 pure/plugin/builder/native checks with the bundled native renderer,
  lint/format/diff checks. Includes invalid IDs/tokens/names/languages/designs/summary
  references, editable blocks, source order, Arabic alignment and fresh English page.
- PASS VISUALLY: All eight final rendered pages inspected across three bilingual designs,
  a graduate fixture without experience, and an academic fixture. Initial Arabic year
  alignment, bullet spacing and complex-script subtitle style corrected and re-rendered.
- FAILED LOCAL INVOCATION: A broader command accidentally included 15 database-dependent
  direct-document cases without their DB fixture; localhost PostgreSQL was unavailable.
  No DB changes occurred. Removed that mis-scoped local invocation; full DB tests remain
  required in the unchanged disposable hosted environment, with no weakened checks.
- HOSTED CHECKS: Required before merge: full PostgreSQL lifecycle, AI cost/review/failure,
  provider pause admission, capture/release/replay, native worker and other-service regression.
  The non-root network-disabled worker gate now also checks three bilingual design fixtures.
- FIRST HOSTED RUN: `38491586305`, job `115617783098`, tested merge tree
  `29ea0e854ae61c17c2af6f7970452419145ee07f`: 1551 passed, one failed, existing ARQ warning.
  The new pause test incorrectly expected `provider_paused`; existing admission correctly
  raises `provider_config` for paused/off AI. Corrected that exact expectation, asserted
  AI is enabled and added zero-cost-hold verification; no production policy was changed.
  Full workflow required on the corrected tree, not a rerun of the failed source.
- NOT RUN: Live provider response, real translation/factual fidelity, native/mobile customer
  acceptance, server deployment, ATS compatibility or employment outcomes.
- FACT: Model responses in tests/visual samples are explicit fixtures, not live AI evidence.
  Reference/token validation and another AI content review do not prove semantic accuracy.
  Content review does not inspect rendered page appearance; final native samples do.
- OPERATIONAL LIMIT: Provider remains paused after the earlier usage overrun; uncertain
  exposure is not settled or deleted by this round. Source qualification does not resolve
  invoices or authorize silently reopening global AI traffic.
- NEXT: Qualify/deploy source, reconcile the old exposure, then test a real CV end-to-end.
  Later selective AI work uses shared needs_ai/cost/review/replay and per-service acceptance.
