# Approved bounded fixes review

Date: 2026-10-04. Task branch: ai/task-20261004-182433.
Starting HEAD: b2f8699 "Fix Compose configuration validation in CI".
Scope: the approved bounded fixes only. No commits, pushes, merges, releases or production
database access were performed. Existing file-retention work (retention.py, storage.py,
roadmap, tests/test_retention.py) was preserved unchanged.

## Fixes applied

1. Private-chat gate. `app/bot/middleware.py` gains `PrivateChatGate`, registered in
   `app/bot/main.py` as an outer middleware for both messages and callback queries. Non-private
   (group/supergroup/channel) updates and callback queries without a reachable message are
   answered with a localized `private_only` message/alert and dropped before any customer
   routing or FSM state mutation. Answer failures are suppressed so the gate never crashes the
   update.

2. HTTPS-only AI endpoint. `app/core/settings.py` rejects an `http` (or non-HTTPS) `ai_base_url`
   when `ai_enabled` is true, after the existing URL sanity checks. `http` remains tolerated for
   a disabled AI configuration (local/model development).

3. Truthful draft-cancel text. New `draft_cancelled` key (ar/en); the FSM draft cancel paths
   (`cancel` inline button and `/cancel` command) now say "draft cancelled, no credit reserved or
   charged" instead of the financial `cancelled` text. The financial rejection path
   (`reject:` callback, `confirm_structure(..., False)`) is unchanged. The `cancel` callback also
   removes the stale draft's inline keyboard (`edit_reply_markup`) best-effort. The `choice`
   handler no longer silently swallows a stale-key mismatch; it answers an `invalid_request` alert.

4. Support delivery. `app/bot/ops_handlers.py` now delivers to each admin independently (one
   failing transport does not abort the others), reports `support_sent` only when at least one
   payload was copied, and reports `support_failed` otherwise (including the no-admin case). The
   ticket id is preserved in FSM state (`ticket_id`) across retries so a retry reuses the same
   ticket instead of creating duplicates. `/reply` now reports `support_reply_failed` to the admin
   instead of crashing when the customer send fails.

5. Retryable intake I/O. `app/files/telegram.py::receive` wraps Telegram download and storage save
   in a guard that re-raises `ServiceError` (validation/limits) unchanged but converts any other
   transport/IO failure into `ServiceError("input_retry", transient=True)`. The intake handler
   already stops on `ServiceError` without advancing state or reserving, so a retry is clean.

6. P2 — user admission cap label. `app/ops/costs.py::check_admission` now raises `user_cost_cap`
   for the per-user limit and keeps `cost_cap` for the global limit.

7. P2 — stale removed-plugin enablement. `app/ops/admin.py::set_service` now uses
   `registry.types.get(slug)` and raises `ServiceError("unavailable")` (instead of an unhandled
   `KeyError`) when enabling a DB row whose plugin was removed from the registry.

## Changed files

- app/bot/middleware.py, app/bot/main.py (private-chat gate)
- app/core/settings.py (HTTPS gate)
- app/i18n/ar.json, app/i18n/en.json (`private_only`, `draft_cancelled`, `support_failed`,
  `support_reply_failed`, `input_retry`)
- app/bot/handlers.py (draft-cancel text + keyboard scoping; choice non-silent)
- app/bot/ops_handlers.py (per-admin support delivery, reusable ticket id, safe /reply)
- app/files/telegram.py (retryable intake I/O)
- app/ops/costs.py (user cost-cap label)
- app/ops/admin.py (stale-plugin enablement)
- tests/test_bounded_fixes.py (new: 14 regression tests)
- tests/test_bot_flow.py (one assertion updated for the truthful draft-cancel text)
- ENGINEERING/MASTER_ROADMAP.md, AGENTS.md (accurate NOT RUN record)

## Verification status

- Tests: NOT RUN. This environment has no pytest binary and no `pytest` module
  (`pytest --version` and `python3 -m pytest --version` both fail), so the regression tests are
  authored but unexecuted here. They require the disposable `*_test` PostgreSQL/Redis used by
  `tests/conftest.py`.
- Lint/format (`ruff check .`, `ruff format --check .`): NOT RUN (ruff unavailable; general shell
  denied).
- `git diff --check` (whitespace): PASS (tracked files only).
- Static review: PASS (read-only). No migrations added; no service list or core-policy branching
  introduced.

## Residuals

- Middleware registration order between `PrivateChatGate` and `Guard` is not asserted here; both
  block non-allowed updates, so the security property holds under either order, but the exact
  wrap order was not runtime-verified.
- A support ticket is still committed when no admin is configured (`support_failed`); the ticket
  is reused on retry rather than duplicated.
- Stale draft buttons from a `/cancel` command (not the inline button) are not removed because the
  command message has no reference to the earlier prompt messages; they are neutralized by the
  state filters and the `invalid_request` fallback.
- File-retention concurrency reasoning remains as recorded in the separate
  [file-retention report](2026-10-04-file-retention-safety.md).
