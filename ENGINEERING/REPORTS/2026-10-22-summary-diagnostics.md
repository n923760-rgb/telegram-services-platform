# Summary rejection diagnostics

Baseline: official main 497edd976b7f8ee32764df659c62d0c32951b85f.
Owner authorizes ongoing service quality improvements and merging ready work.

## Observed result

Operator reports five passing representative cases and one failed summary in
`/home/aidev/service-acceptance-hKpgdXBw`, test database
`svc_6a69a6255e1d_acceptance_test`. Both summary generation attempts failed with
`constraint` before semantic review. The report does not identify which validator
failed or retain the model candidate. Its exact cause remains UNKNOWN.

The run reports ten calls, calculated usage 0.016179 SAR (not invoice evidence),
conservative call exposure 0.437433 SAR, zero active orders and reserved synthetic
credit. Production provider pause remains true according to operator output.
Passing editing, translation and native document results still require actual
ZIP inspection. No claim of semantic readiness from the PASS count alone.

## Bounded change

Replace generic ValueError types with fixed PydanticCustomError codes for the
existing seven logical summary checks: point limit, source IDs, clean point text,
duplicate points, numeric/contact fidelity to cited source, output character
limit and source compression. Declare these codes through the existing gateway
diagnostic API. Do not add a summary-specific branch in core or gateway.

The gateway already sends fixed categories and a bounded invalid candidate to
the single in-memory correction attempt. Specific labels now make that existing
feedback meaningful. It still records no candidate/source text, values, exception
messages, paths or context in isolated diagnostics. All validation conditions and
ordering remain; point-text exceptions retain the same
rejection behavior. Input/output JSON schema, accepted payloads, service version,
prices/gates and prepared replay are unchanged.

## Checks and remaining work

- PASS locally: 49 focused checks including 15 new tests. Exercise every logical
  category, unknown/duplicate references, new/repeated numbers and changed contacts,
  malformed paragraph text, output/compression limits, unchanged public schema,
  and accepted correction versus persistent failure after exactly two calls with
  per-call reservation/settlement mocks. These are scripted provider checks.
- Require hosted full tests, migrations, lint/format and native worker qualification
  before merge; no production provider call was made here.
- After merge, build the worker image and rerun only `summary` through the existing
  isolated wrapper. This build does not replace running production containers.
  Preserve old backups/accounting and production pause; do not increase budgets,
  relax fidelity/compression or add retries to manufacture a PASS.
- If the rerun still rejects, use the fixed category to investigate the actual
  failure class. If it passes, inspect the summary and references against all
  twelve source paragraphs before declaring the sample ready.
