# Service menu and confirmation layout — 2026-10-10

- OWNER AUTHORITY: Remove prices from service buttons, show price separately at confirmation, and improve related presentation; continuous verified merge authority persists.
- FACT BASELINE: main aef8b6a / PR #41, 904 tests and seven document-worker gates passed.
- CHANGE: Menu controls show only the registered localized service name. The menu explains that price is shown before confirmation. Existing authoritative intake price snapshots, server-side stale-price checks, Stars eligibility, terms and callback IDs remain unchanged.
- CHANGE: SAR and Stars price is a separate first line followed by a blank line before payment details. Stars purchase terms remain present and unchanged. PDF-table workbook instructions use one sheet per bullet instead of a dense mixed-direction sentence.
- PASS LOCAL: 27 UI unit checks; lint, formatting and diff checks; 912 tests collected.
- NOT RUN LOCAL: PostgreSQL dispatcher/payment regression tests; full hosted CI must qualify these and all seven native document gates before merge.
- NOT RUN: Server installation and device/font visual acceptance. User screenshot supports previous short-reference/full-width UI deployment only; no blanket runtime health claim.
- No pricing, ledger, payment policy, schema or dependency changes.
