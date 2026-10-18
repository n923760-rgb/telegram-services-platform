# Inline summary source references — 2026-10-18

## Baseline and bounded scope

FACT: Official main 41b0865aef69a283266d7dc861ead5d60f188087 includes #102.
Owner authorizes continued improvements and merge after qualification, with production
deployment deferred to one later batch. This round improves summary traceability only.

## Contract

CHANGE: TextSummary v3 renders each point as a numbered bullet followed by a localized
Source paragraphs line. Source IDs are displayed ascending without mutating the validated
AI plan. The attached report begins with the identical summary and repeats the same
mapping in its point-reference index. Original numbered source paragraphs and full normalized
original appendix remain unchanged, including blank lines, leading zeros and contacts.
Point numbers and source paragraph numbers are separate namespaces with explicit labels.

SAFETY: No new AI call, schema, prompt, semantic review, retry allowance, migration,
dependency, customer input, artifact or administrator price/activation change. Version guards
release/cancel unprepared legacy work and reuse already prepared results as before.

## Verification

PASS LOCALLY: 45 summary/service/source-reference tests; three architecture gates,
global Ruff lint/format, diff whitespace, YAML and embedded worker Python syntax.
Dense case covers seven points with all 80 references, unchanged plan/source, valid Result
and multipart Telegram limits. Other cases cover AR/EN labels, nonconsecutive/reversed IDs,
distinct point/source numbering, exact source appendix and existing provider failures.
An initial new test treated the message-parts generator as a list; corrected the test to
materialize it before publication. No production code change was needed for that correction.

Added/extended hosted PostgreSQL/Redis tests cover unchanged bounded repair/capture/cost,
v1/v2 cached legacy summary replay without provider calls, and cancellation/release of
unprepared v1/v2 orders while retaining administrator overrides. Native non-root offline
worker qualification additionally checks bilingual mappings and UTF-8 report/source fidelity.
Full exact-head hosted workflow required before merge; local checks alone are not qualification.

LIMITS: References identify nonempty physical source lines, not sentence-level proof or a
guarantee against omitted/reversed meaning. Existing semantic review remains responsible
for its bounded checks. No live-provider/mobile visual acceptance or server deployment run.
