# Complete minutes review — 2026-10-13

Owner continues verified development and merges. Baseline main `89d1508` / PR #65;
runtime deployment, actual provider/mobile acceptance and payment qualification
remain separate and are not assumed complete.

## Problem and implementation

FACT: The structural review showed only two samples per category and shortened
task owners/deadlines to 40 characters. Later tasks and deadline conditions could
therefore be absent from the customer's approval message.

Add optional generic `Result.review_details` and AR/EN localizations, each bounded
to 50000 characters. Keep the short-preview limit at 3000. Display details only
while `needs_confirmation` is true, using the current UI language and falling
back to the ordinary preview for legacy results. Existing UTF-16 message splitting
and last-message-only buttons serve both notifications and owner-bound order details.
No service slug or new approval policy is introduced in core/adapters.

MeetingMinutes supplies every classified source slice exactly once, grouped by
category, with complete same-source owner/deadline spans or explicit unknowns.
Repeated notes retain distinct IDs. Show the customer title, review instructions
and final approve-or-cancel instructions; do not paraphrase/translate the source.
Ordinary four-note reviews remain compact; long reviews can span many messages.
No provider call, file creation or capture is added before approval.

## Compatibility and bounds

Input schema, version 3 and classification continuation are unchanged. Existing
queued work uses the current display; already cached reviews keep their original
legacy preview. Approved continuation and prepared artifact replay are unchanged.
No migration, dependency, price/default flag, activation, financial or provider
policy change. Standard content purge still removes the JSON result column.

Each source span occurs once and metadata is bounded by its same source note;
the 12000-character/80-note input plus quoted metadata fits the 50000-character
review bound. Telegram parts stay within 3500 UTF-16 units. Notification is
at-least-once: a partial transport failure can repeat earlier messages on retry,
but does not trigger new AI work or early capture. No claim of exactly-once UI.

## Evidence and later qualification

PASS locally: 39 review/schema/preview/DOCX cases, 19 existing pure service cases,
three architecture gates, lint/format/diff. One existing native resume/export case
is excluded only in a temporary local test copy and stays enabled in full CI.
Full suite collects 1334 tests. PostgreSQL/native runtime checks NOT RUN locally.

New hosted DB cases exercise complete AR/EN order-detail reopening, failed middle
message recovery and both approval/cancellation settlement with one AI call.
Retained native export tests inspect approved source-bound Word/PDF. Full hosted
financial/native workflow on the final source is required before merge.

Actual Telegram mobile readability, provider classification accuracy and runtime
deployment NOT RUN. Later trials should compare the last task and full conditional
deadline in review/Word/PDF and switch UI language without translating source text.
In-place task editing is not implemented; cancellation/re-entry is explicit.
