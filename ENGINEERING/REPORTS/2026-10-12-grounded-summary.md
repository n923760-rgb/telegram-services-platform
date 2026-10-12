# Grounded text summaries — 2026-10-12

## Problem and scope

The owner trial selected five of six paragraphs, retained a superseded launch date,
and omitted the next meeting. A natural single-paragraph input was rejected by the
two-line extractive contract. Replace that contract with one bounded summary outcome.

## Implementation

- v2 accepts one to eighty nonempty lines, maximum 12000 characters; specific safe input error.
- One validated JSON plan contains up to three/seven concise points in requested AR/EN.
- Each point cites unique known source paragraph IDs. Numeric and contact tokens must
  occur within cited paragraphs, including exact date notation and leading zeros.
- Duplicate points, invalid characters/newlines, overlong output and long-source
  summaries with no word-count compression are rejected before saving artifacts.
- Existing production AI gateway reviews final decisions, rejected proposals, source
  meaning, responsible people and deadlines; at most one correction, accounted calls.
- Message contains the summary. Owned TXT contains summary, point references, numbered
  source and original normalized source text. CRLF normalization remains existing policy.
- Default disabled, manual prices and enabled overrides unchanged; no new dependencies,
  financial changes, migrations, payment or VPS actions.

## Evidence and limits

- Local schema/storage tests: 35 PASS; full lint/format and diff checks PASS.
- PostgreSQL lifecycle tests cover valid/invalid plans, repaired schema, cached delivery,
  save failure, admission bounds and semantic review acceptance/rejection with cost/credit
  settlement. New reviewer fixtures include omitted meeting, superseded date/approved
  rejected budget and invented assignee, which numeric validation alone cannot detect.
- Full hosted exact-head workflow required before merge; not represented as local DB evidence.
- No actual model call or customer acceptance for v2. Fixture verdicts prove gateway
  behavior, not that a model will reliably recognize every semantic defect.
- Original evidence is retained for inspection; citations, subset numeric validation and
  word-count compression cannot certify facts, entailment or complete important coverage.
- Existing version policy settles unprepared v1 jobs; prepared/cached results retain delivery.

## Runtime acceptance after deployment

Try the owner's six-sentence scenario as a single paragraph and as multiple lines.
Require final launch 27-10-2026, unchanged budget 3500, rejected 5000 proposal, Khalid/Sara
deadlines 24/25-10-2026 and next meeting 26-10-2026. Repeat in English and check a
source containing uncertainty, negation, leading-zero IDs and contacts. Inspect owned
report for source/reference integrity; do not certify all services from this trial.
