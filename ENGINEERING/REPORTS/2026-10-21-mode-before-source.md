# Choose processing before supplying source — 2026-10-21

## Source and bounded change

FACT: Official main `1688401d8905819d4f2e5d19596e44737dbe69f7` warns from
the first mixed-service prompt and blocks unavailable choices. Text PDF and PDF
tables still ask for their source before the processing choice. This is the
remaining mode-before-source portion of R04; owner requests continued development.

CHANGE: Text PDF v5 collects mode, text, then the existing optional direct-mode
title. PDF tables v5 collects headings mode, PDF, language, then the existing
optional Arabic-order choice. Selected values, required/optional fields, source
limits, confirmation, review/edit and processing implementations are unchanged.
The existing generic bot renders these schemas; no new bot branches or dependency.
AR/EN PDF text prompts no longer promise a subsequent mode question, and remain
neutral for old source-first drafts.

All four current mixed services now collect the AI-dependent choice before the
initial source input. Unavailable processing is marked and blocked before source
intake using #127's current pause/AI flag checks. No forced direct fallback. A
later pause or other admission limit can still reject final confirmation.

## Compatibility and operations

The input order is a persisted conversation contract, so both versions increase
from 4 to 5. Registry sync preserves administrator activation, SAR price and Stars
price. Saved v4 schemas/positions remain intact during resume and are not silently
reinterpreted as the new order. Their old-version confirmation rejects without a
purchase or reservation; the customer must start a current-version draft.

Under existing worker version policy, already-prepared historical files can replay
without rendering/extracting again; unprepared historical orders cancel and release
their credit. No new compatibility exception or financial rule is introduced.
Drain outstanding work before an eventual deployment to avoid this existing
cancellation path. Production state is UNKNOWN here; no server action was run.

## Checks and limits

PASS LOCALLY: 161 focused availability/intake/review/edit/policy checks (22 new),
three executable architecture gates, global ruff lint/format and diff checks.
New tests cover all five affected processing choices in AR/EN, rejecting typed
source before mode, unavailable choice preservation, direct progress, v4 positions,
failed-send recovery and editing/return without losing the existing source.

139 affected dispatcher/lifecycle/upgrade tests collected; NOT RUN locally because
PostgreSQL is unavailable. Fourteen new DB cases cover disabled AI versus provider
pause before source, old draft confirmation with zero Order/CostHold/StarCharge or
reserved credit, and v4 prepared/unprepared upgrades for both services. Existing
direct capture, exact content, optional title, replay, older upgrades and current
pause/resume tests are updated for the new schema/version. Exact-head hosted full
tests, migrations and native worker qualification are required before merge.

This improves intake timing, not generated-document quality. No provider calls,
production setting/activation changes, price changes, dependency, migration or
deployment. Live Telegram, provider semantics and mobile/Office acceptance remain
separate qualification gates.
