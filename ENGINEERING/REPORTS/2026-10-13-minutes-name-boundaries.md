# Meeting note name boundaries — 2026-10-13

Owner requests continuing Telegram Services Platform from the last development
conversation, retaining earlier authority for verified development and merges.
Baseline: main `5321530` / merged PR #64. No VPS deployment is assumed.

## Finding and change

FACT: v2 splits `Dr. Sam` and `د. أحمد` after the title dot, making it impossible
to quote the complete owner from a single source unit. Regression tests reproduce
the title/initial/list failures before the fix.

MeetingMinutes v3 conservatively keeps common AR/EN titles, uppercase initials,
dotted Latin abbreviations and a leading one-to-three-digit list marker together
with their following text. Explicit newlines remain authoritative. Original slices,
internal whitespace, duplicate notes, numeric/date notation, sentence punctuation
and the 80-unit/1200-character/12000-total bounds remain in effect.

This is bounded lexical protection, not general linguistic sentence detection.
Unknown abbreviations can still split; abbreviations at actual sentence ends can
retain a mixed unit. The existing production AI review must classify uncertainty
as review, without inventing assignments or joining separate ambiguous units.

## Compatibility and checks

Version 3 is required because unit IDs and approved metadata interpretation change.
Existing generic policy cancels unprepared v1/v2 work and releases test credit;
approved-but-unrendered continuation follows that same policy. Prepared artifact
delivery replays without reclassification, rendering or new provider calls.
Registry sync retains administrator enablement and SAR/Stars prices. No new
dependency, database migration, provider/payment policy, core branch or activation.

PASS locally: 27 schema/preview/DOCX tests, 19 existing pure service cases, three
architecture gates, repository lint/format and whitespace checks. One existing
native-render service case was excluded only from the local temporary test copy;
it remains enabled in the unchanged full hosted suite. Local PostgreSQL/native
runtime qualification NOT RUN; source-bound hosted workflow is required before merge.

Hosted additions cover single capture and native AR/EN export after approval,
v1/v2 cancellation with retained costs/prices and idempotent cached file delivery.
The non-root/network-disabled native worker gate additionally exports titled
owners with exact source IDs/numbers/deadlines. No existing CI gate is removed.

Real-provider semantic/visual quality, Telegram/iPhone acceptance and VPS update
remain NOT RUN. Before later deployment, drain or explicitly resolve unfinished
minutes jobs; trial titled names, rejected dates, repeated notes and leading-zero
identifiers, then compare preview, Word and PDF. Payment qualification remains last.
