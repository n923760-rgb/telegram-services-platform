# Selected summary point limit

Baseline: official main 6d7323b94b3a61a2277b9fd568d4adea93019b36.
Authority: owner authorizes ongoing quality improvements and merging ready work.

## Observed evidence

The operator's summary-only run uses backup `/home/aidev/service-acceptance-10GsKnme`
and test DB `svc_76a1495edfc4_acceptance_test`. The uploaded ZIP contains only
`results/report.json`, no customer deliverables. It records two generation
rejections with `summary_point_limit`, zero active orders/reserved synthetic
credit, settled cost holds and calculated usage 0.005908 SAR, not invoice evidence.
No rejected candidate or exact point count is available. No successful output or
semantic acceptance can be inferred from this failed run. The earlier five passing
results have not been uploaded in this attachment and still need inspection.

FACT: `Inputs.limit()` and the prompt require at most three points for short
summaries, but the generated `SourceSummary` inherits `Summary.points` with
JSON Schema maxItems=7. The same contradictory declaration is sent on correction.
The after-model validator correctly rejects a fourth point; it must remain strict.
INFERENCE: The contradictory provider declaration can contribute to overlong
responses. The unavailable exact rejected text prevents attributing every model
decision to that declaration alone.

## Fix

Override the generated points field with the selected limit: maxItems=3 for short,
7 for standard, retaining minItems=1. Keep the source of truth `Inputs.limit()`;
do not infer limits from source content. A before-field validator preserves the
fixed `summary_point_limit` diagnostic on JSON arrays exceeding that bound,
including more than seven points. The existing after-model guard remains for
other supported Pydantic input paths. Validation order now reports array overflow
before validating individual points, without changing the accepted payload set.

Initial generation and correction use the same generated schema class, with no
shared mutable request limit. No prompt expansion, provider-specific code, content
truncation, added call allowance or silent removal of facts. Keep references,
numeric/contact fidelity, paragraph hygiene, compression, semantic review and
all existing accounting/cleanup policies. The provider schema intentionally
changes; public inputs, accepted outputs and service version stay the same.
Prepared historical results replay without regeneration.

## Checks and remaining work

- PASS locally: 58 focused summary/reference/acceptance checks, nine new cases.
  Both languages and lengths enforce the selected boundary; schema generation
  across short/standard/short requests does not leak a previous limit.
- PASS locally: Four scripted real-gateway cases check the same maxItems on initial
  and corrective generation, a valid corrected summary followed by review, or two
  invalid generations without review. Existing per-call reservation/settlement
  runs on each call; diagnostic events contain no source/candidate text.
- PASS locally: Three architecture gates and global lint/format/diff checks.
- ADDED, NOT RUN locally: Two PostgreSQL scenarios exercise four-point rejection,
  corrected delivery or terminal failure, one capture/release, two settled usage
  records, replay without new calls and file cleanup. PostgreSQL unavailable here.
  Require exact-head hosted verification before merge.
- NOT RUN: Real provider after this fix. Build the updated worker image, then run
  only summary through the existing isolated wrapper. Preserve production pause,
  run/per-job budgets, backups and failed-run accounting. Do not replace production
  containers just to execute this isolated test. Inspect any resulting summary
  against all twelve source paragraphs before claiming sample readiness.
