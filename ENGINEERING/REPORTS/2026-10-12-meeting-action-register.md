# Meeting action register — 2026-10-12

Owner directs development first, manual acceptance later, payment last.

## Change

MeetingMinutes v2 accepts connected notes or lines, separating sentence punctuation
followed by whitespace without splitting decimal dots. Quote resulting units; preserve
duplicates, reject rather than truncate beyond 80 units/1200 characters each/12000 total.

Every unit is classified once. Action-only assignee/deadline fields must quote the same
source unit and preserve whole numeric tokens. Word/PDF retain source paragraphs and
add reference/assignee/deadline columns; unknowns explicitly show Not specified.
Bilingual approval preview includes metadata samples. Production AI review checks
classification, explicit metadata coverage and correct role/date meaning, with existing
bounded/accounted correction. Approved continuation is revalidated, no second AI call.

No prices/default activation/payment changes, dependencies, migration or core branching.
Existing version policy remains; actual service activation and deployment not performed.

## Evidence / limits

31 local source/schema/DOCX/preview tests PASS. One retained existing real LibreOffice
render/resume case not run locally; full hosted qualification must run it, not skip it.
New DB tests exercise semantically wrong source-present owner/date, review repair or
refusal, provider costs, reservation release/capture and export only after approval.
Native non-root/network-disabled workflow adds AR/EN action metadata and exact deadline
export assertions. Full exact-head hosted financial/native workflow required before merge.

Fixture verdicts demonstrate orchestration, not model accuracy. Numeric/span presence
does not prove correct assignment. Sentence segmentation can split abbreviations;
ambiguous fragments require review, never invented cross-unit associations.
Native rendering checks do not replace manual visual QA or real-provider acceptance.

Later trials: AR/EN connected paragraphs with leading-zero IDs, decimals, rejected
decisions, explicit task owner/deadline and unknown metadata. Compare approval preview,
source paragraphs, action register and dates in Word/PDF; current price/flags retained.
