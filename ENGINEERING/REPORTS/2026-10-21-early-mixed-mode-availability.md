# Early mixed-mode availability — 2026-10-21

## Source and scope

FACT: Official main `06d900fdd5c9c8e42b7af9ca657f497fc1cb13ae` contains
required-AI catalog/start/resume guards and final admission, but mixed services
still offer temporarily unavailable processing choices without marking or blocking
them until submission. Owner requests continued review improvements. This bounded
round addresses the early-warning/choice portion of R04, without changing intake
contracts or moving fields in persisted drafts.

## Change

- Add validated, plugin-owned `ai_intake_choices` UI declarations. Four conditional
  services declare Excel/smart document processing and suggested table headings.
  The generic bot does not branch on service identity or invoke `needs_ai` with
  invented partial input. Registry discovery rejects malformed declarations.
- When AI is disabled or the provider pause guard denies admission, AR/EN prompts
  warn from the first question and mark affected choice buttons unavailable.
  Keep direct choices and existing callback values/order. Recheck on click so old
  buttons reflect a new pause or resume. Reject the unavailable selection without
  changing inputs, price, purchase key, edit snapshot or collection position. An
  optional skip alias to a marked choice cannot bypass the UI guard.
- Generic editing uses the same guard and retains return-without-changes. There is
  no automatic switch from smart to direct processing. Unmarked direct choices
  and the existing legacy direct skip continue normally.
- Apply declarations only when the current plugin version and complete normalized
  input schema match the saved draft. Historical/different schemas retain existing
  intake behavior and the authoritative final admission/version protections.

## Validation

PASS LOCALLY: 139 focused policy/availability/intake/review/edit tests (35 new),
three executable architecture gates, global ruff lint/format and diff checks.
Tests cover both languages, current metadata against complete validated mixed-mode
requests, invalid declarations, stale schema/version, disabled-AI no-DB behavior,
pause/resume rechecks, first source prompts, direct/legacy skip and edit restoration.

Ten new DB/dispatcher cases exercise every declared mixed choice in both languages,
including pause after displaying an enabled button, no Order/CostHold/StarCharge or
credit reservation on rejection, unchanged source/price/key and resumption with the
same callback. Existing navigation assertions now expect the early block and
marked button; the Excel path explicitly enables AI. 77 affected dispatcher cases
collected; NOT RUN locally because PostgreSQL is unavailable. Exact-head hosted CI,
migration checks and native worker qualification are required before merging.

## Limits and preserved boundaries

Availability is a read-only hint for AI_ENABLED/provider pause, not full admission
or a provider health check. Final confirmation still validates configuration,
service state, limits, budgets, prices and current input; a later pause can still
reject submission. Source-first services keep their current order: early warning
precedes the text/file question, but mode selection is not moved before the source.
Moving it requires a separately versioned intake change. Not every R04 item is
claimed closed.

No changes to InputSchema, service versions, prices, activation, financial/provider
policy, dependencies, migrations or production. No live Telegram/provider calls,
server deployment or native/mobile quality certification. Mocked UI tests and
synthetic native checks remain distinct from live acceptance.
