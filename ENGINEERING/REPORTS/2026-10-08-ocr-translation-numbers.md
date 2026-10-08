# OCR translation numeric fidelity — 2026-10-08

## Authority and source

OWNER REQUEST: Merge mixed-PDF PR #19 and continue professional output improvements.
FACT: #19 merged as `6415e57da8cec22d198c4bd941d4ffa864dc3c98`; main workflow
`37831298533`, job `113497016943`, passed 355 tests, lint/format, migrations/drift and
Compose validation. Actual logs contain one existing ARQ deprecation warning.
No server deployment was performed.

## Problem and bounded implementation

FACT: Translation previously validated only JSON and text length. A valid string changing
`00123` to `123`, `125.50` to `250.50` or dropping a date would pass that model and could
be delivered/captured. Provider prompt instructions alone do not detect these errors.

Compare a multiset of literal numeric tokens in the translated text against extracted text.
Tokens include digit runs, common numeric separators, signs, dates/fractions/ratios, percentages,
Arabic-Indic digits and numeric portions embedded in identifiers. Preserve notation, leading
zeros and occurrence counts; permit sentence reordering, not numeric addition/deletion/reformatting.
JSON Schema instructions explicitly request this behavior and no unit/currency conversion.

Bind validation in a request-local Pydantic subclass passed through the existing injected AI
gateway. No source values appear in JSON Schema or shared mutable models. A mismatch is a
schema validation error, so the existing one repair applies; two invalid translations fail
`provider_invalid`. No new provider calls/retry loops outside existing policy.

Contract version 2 records this stricter accepted-output behavior. Input fields, price,
default disablement, extraction prompt, renderer, providers, ledger and DB schema are unchanged.
Unprepared version-1 orders cancel/release through existing policy; admin settings remain intact.

## Evidence and limitations

PASS: Locked install, lint/format and 26 focused schema/plugin/governance tests (22 new
schema cases). Covers changed amounts/dates, missing/extra numbers, precision/zeros/percent signs,
ten multilingual numeric forms, duplicate counts, sentence reordering, invented numbers without
source numbers and isolated request contracts. Full suite collects 383 tests (28 new cases).

NOT RUN locally: Full PostgreSQL/Redis suite. Six new hosted cases cover ordinary/repaired
translation, exhausted repair with release/notification once, recorded cost per attempt,
cached long TXT/editable DOCX delivery retry, untranslated OCR and old-version cancellation
with preserved admin settings. Inspect source-bound hosted logs before merging.

UNKNOWN / NOT RUN: Real OCR and translation/source-fidelity, native Word visual acceptance
and new Telegram/server runtime. Numeric equality cannot detect swapped amount/name associations,
changed names, units/currency or omitted prose, or correct an OCR error in the extracted text.
Embedded identifier letters are not checked. This is an additional guard, not semantic fidelity.
Conservative literal tokenization can reject otherwise equivalent formatting/localization,
including punctuation adjacent to numbers. Such normalization is intentionally not supported.
No newly rendered document or paid-launch qualification is claimed in this code round.
Use [output quality gates](../../docs/OUTPUT_QUALITY.md) for remaining acceptance.

## Hosted fixture correction

FAIL: Initial head `350307d` workflow `37832221571` reported 380 passed and three failures.
Two new fixtures were incorrect: the 50-record translation was only 3,449 characters after
trimming (below the >3,500 file-delivery threshold), and the no-translation order supplied an
inactive style field. An existing cancellation test hard-coded version 2, which now matches
the actual plugin instead of simulating a version change. No application failure was found.
Correct fixtures to 60 records with an explicit threshold assertion, omit the inactive style,
and derive a distinct next version from the current plugin. Rerun the full final-head workflow;
do not treat the initial run as passing evidence. No application/governance rule was weakened.
