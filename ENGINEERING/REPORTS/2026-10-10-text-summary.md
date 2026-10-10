# Extract key points from source — 2026-10-10

## Authority and verified baseline

FACT: owner asked to continue the independent useful-services expansion; prior
continuous verified merge authority applies. Main e624000 / PR #38 passed automatic
post-merge workflow 38070202160/job 114265871891: 785 tests, lint/format, migrations,
drift, Compose and all six non-root/network-disabled native worker gates. Logs reviewed.
This round adds one bounded plugin, not deployment or automatic live activation.

## Product contract

`text_summary` v1, AI required, disabled by default. SAR 3.00 is an administrator-issued
test-credit default; no Stars price/terms or DB-owned service overrides are changed.
User supplies pasted Arabic/English/mixed source, one paragraph per line, 2–80 nonempty
lines, <=12000 characters. Normalizes CRLF/CR to LF, rejects blank/control/surrogate/
noncharacter input. One-paragraph blobs must be split by the user; no guessed sentence
boundaries, uploaded-file reconstruction, rewritten summary or study questions.

Short selects up to 3 points, standard up to 7; actual cap is also source count minus one.
AI receives numbered paragraphs as untrusted JSON data and returns source_ids only.
Request-local strict schema rejects unknown/coerced/duplicate IDs, empty/over-limit
selections and every additional field, including invented prose or rationale. Source
content is not in schema/errors. Existing abstract provider budget and one repair reused.

Output copies full selected paragraph strings in original source order with references.
No AI-generated prose, values, contacts, names or dates become output content. Fixed
localized headings describe selected/total counts and omitted-context limitations.
Chat text plus one owned UTF-8 summary-source.txt containing points and every numbered
source paragraph. Empty lines are separators, not source IDs; original paragraph edge
whitespace is retained. Report heading language does not translate customer content.
No bot/core/wallet/order branches, dependency, migration or vendor SDK introduced.

## Verification and limits

Unit coverage: exact source strings/order/references/report, source/schema separation,
strict bounded IDs and no generated extra fields, invalid source/choices before AI,
request isolation, large input/report bounds, abstract injected provider, AR/EN headings,
owned UTF-8 output and cross-owner rejection, unavailable/failed provider creates no file.
Real-DB lifecycle cases: both report languages/lengths, one repair, capture once, failure
release, unknown/duplicate/generated/full-source response failure, disabled AI and invalid
paragraph admission, storage failure, cached delivery without another provider call and
terminal file retention. Full hosted tests and native worker qualification required on
published head before merge. Local DB/Redis unavailable; no shared fixture is weakened.
PASS LOCAL: 90 DB-independent source/service/architecture checks using --noconftest,
ruff check/format and diff check; 829 tests collected (30 new unit / 14 new DB cases).
Final qualified workflow/job and actual test count recorded on the PR before merge.

NOT RUN: live-provider point relevance, source-context completeness, customer willingness
to pay, Telegram/operator installation, service enablement and commercial Stars acceptance.
Extractive quotes do not guarantee a correct overall impression: omitted conditions,
exceptions or negations in another paragraph can materially change meaning. No claim of
comprehensive summary accuracy or a compression ratio (headings/report add characters).

Before enablement compare output against full source on Arabic/English/mixed notes,
repeated facts, references to other paragraphs, dates/zeros/amounts/contacts, negations,
conditional claims/exceptions in separate paragraphs, instruction-like prose and lengthy
uneven paragraphs. Test both caps, heading languages, malformed response repair, quota
failure and delivery retry. Record usefulness and omissions, not only ID correctness.
Abstractive summaries, revision questions and CV writing stay separate future contracts.
