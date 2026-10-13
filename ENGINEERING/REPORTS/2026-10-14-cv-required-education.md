# Required education in CV intake

## Authority and incident
Owner explicitly requested removal of skip for necessary CV content after a failed
bilingual confirmation. Baseline e19f746 / CV v3 deployed successfully by operator.
Read-only owner-draft metadata showed education and experience absent in BOTH bodies;
intake validation passed but nested English content validation rejected submission.
No raw career/contact content was requested or copied into this report.

## Changed policy and implementation
CV v4 requires a supplied education qualification/stage in each requested language.
Experience remains optional so students/graduates need not invent work experience.
Root and nested English input fields are required; existing generic bot intake omits
skip and rejects forged skip callbacks without advancing or altering the draft.
Pydantic content also requires education, even when experience exists, aligning
intake and final submission instead of allowing an invalid confirmation path.
Localized prompts explicitly state education is required and experience can be skipped.
This intentionally replaces v3's at-least-education-or-experience policy; no core change.

## Safety and compatibility
Input contract version increments to 4. Prices, activation, provider pause, templates,
artifacts and financial behavior unchanged. No dependency/migration/raw Redis mutation.
Old unprepared v3 orders/drafts follow existing stale-version rejection/cancellation;
prepared artifacts follow existing replay recovery. Deployment must check active orders.

## Evidence and limits
PASS locally: 66 focused pure CV/Word-PDF/architecture cases; lint/format/diff.
New unit cases cover missing education despite experience and graduate inputs without
experience. Hosted bot cases cover Arabic, English and both bilingual education fields:
no skip button, forged callback rejected, state/data unchanged. Hosted full CI required
before merge. New deployment/Telegram acceptance NOT RUN. Rendering is unchanged.
