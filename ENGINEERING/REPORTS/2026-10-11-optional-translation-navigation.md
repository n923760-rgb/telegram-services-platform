# Optional translation result navigation

## FACT — scope and behavior

Owner reported that the single translation shortcut looked like a required next step.
Baseline main: 7cf4b7cd24a88a53f91d31d03004e6f5ad94d504 (PR #49).
The eligible followup panel now shows Home, Request another service and Translate
text — optional, on separate rows in Arabic and English. Completion wording makes
translation optional and retains separate-order price-before-confirmation disclosure.

Reuse existing menu callbacks and owner-bound followup callbacks. Original OCR
delivery precedes the panel. Existing eligibility checks still determine whether
the followup panel is offered. Navigation does not initiate translation. Clicking
translation still uses normal independent intake and confirmation.

## Verification

Extend the existing delivery journey across both UI languages and both historical
OCR source plugins: verify original text, ordered controls, navigation without a
new draft/order/reservation, and retained source text. Existing lifecycle checks
cover deliberate translation selection and single capture.

Require lint, formatting, pure governance/service checks and full exact-head hosted
PostgreSQL/Redis regression, migration drift and eleven native worker gates before
merge. Record hosted head/tree/run/job evidence in the PR after completion.

## NOT RUN / compatibility

VPS update and real mobile acceptance are not run here. No new dependencies,
migrations, service versions, activation, engine routing, pricing or payment work.
No claim that prompt guidance guarantees OCR fidelity.
