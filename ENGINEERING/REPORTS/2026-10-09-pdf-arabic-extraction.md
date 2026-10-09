# PDF-to-Word Arabic numeric extraction

Baseline: main 1f16d8fb7f473bd7c9b0872f22730b3a98bc53d4.
Scope: recover mixed-direction source text before the PDF-to-Word AI call.

## Evidence

- FACT: The operator's one-page PDF visibly includes order 00123, SAR 125.50,
  English acceptance text and date 2026-10-08. Default pypdf extraction omits
  the Arabic-adjacent order and amount. Reproduced with locked pypdf 6.19.0.
- FACT: pypdf visitor callbacks contain these values even though its final
  returned bidi string discards them. Collect those fragments instead.
- PASS: Generated synthetic real-PDF regression fails before the fix (zero
  occurrences of 00123) and passes afterward, preserving duplicate identifiers,
  zero, missing-value wording, decimals, dates, Arabic and English.
- PASS: Read-only extraction of the supplied PDF retains its order, amount and
  date. The upload is not committed or used as a test fixture.
- UNKNOWN: The earlier provider's exact reason for declining reconstruction;
  recovering omitted text does not prove the next provider call will succeed.

## Implementation and limits

Collect decoded visitor fragments, with a remaining-character budget enforced
inside the callback. Normalize Arabic presentation forms only; do not apply
compatibility normalization to identifiers, digits or other source characters.
Retain page markers, overall length checks, owner isolation, encrypted/mixed/
image rejection and the single existing AI attempt/repair policy.
This does not reconstruct original page layout, OCR, tables or positioned
multicolumn reading order. Model fidelity remains subject to real acceptance.

Increment the PDF-to-Word contract to version 3. Update the upgrade integration
test to exercise version-2 pending work cancellation, release and preserved
admin price/enabled overrides. No wallet policy, dependencies or DB changes.

## Verification

- PASS: 13 plugin/extraction unit tests with locked dependencies.
- PASS: 61 focused PDF/Office/OCR plugin tests in the same locked environment.
- PASS: Local lint/format checks and read-only uploaded-file extraction.
- Hosted full-suite financial/recovery checks: tracked on the task PR.
- NOT RUN: Real-provider retry, native Word opening/editing, production deployment.
