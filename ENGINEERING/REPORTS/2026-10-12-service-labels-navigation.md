# Consistent names and service navigation — 2026-10-12

## Problem and change

The owner's editing trial required clarification because the UI said proofreading and
rewriting rather than text editing. Use one clear customer/admin name and retain
meaningful options inside each service. The summary label was fixed in prior PR #61.

- Text editing, text summarization and text translation are distinct outcomes.
- Short labels describe outcomes rather than implementation or hidden engines.
- CV and meeting services promise formatting supplied facts, not invention.
- PDF tools describe supported merge/page extraction; no unsupported compression promise.
- Root categories: text, images, document creation, PDF conversion/tools, data, CV/minutes,
  followed by existing additional/verification services when available.
- Plugin menu_order metadata produces shared stable bounded browsing with generic
  fallback for future plugins; no slug branching in bot/core policy.
- PDF-to-Word moves from creation to PDF presentation. Existing callbacks and intake
  remain compatible. Unknown/default-order ties retain the supplied stable row order.
- Manage services opens status/activation/price details; Service prices opens price
  editor. Management pages show total pages; details include the service's category.

## Compatibility and evidence

No changes to input schema/version, execution, migration, dependencies, provider calls,
financial policy, activation/defaults or prices. Existing registry sync updates names;
administrator overrides and historic service identities remain intact.

Local pure ordering/readiness tests: 26 PASS. Hosted lifecycle tests verify old labels
are refreshed without changing price/flag/version/schema and customer/admin labels
match. Router browsing preserves draft content and creates no orders/price audits.
Existing category pagination, stale callbacks, permission and financial tests retained.
Full exact-head hosted qualification required before merge; no actual mobile/VPS
rendering or activation performed here.

After deployment use /services and /admin, check text names and PDF conversion placement,
category/next/back navigation, preserved active draft and owner prices/flags. Old Telegram
messages keep their historical visible text; generate a fresh menu to see updated labels.
