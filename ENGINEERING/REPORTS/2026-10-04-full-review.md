# Full review: second bounded-fix round (draft recovery, upload quota, cancel scoping)

Date: 2026-10-04. Task branch: ai/task-20261004-182433.
Starting HEAD: b2f8699 "Fix Compose configuration validation in CI".
Scope: the approved second bounded-fix round only. No commits, pushes, merges, releases, secret
changes or production database access were performed. Existing uncommitted work (the earlier
bounded fixes and the file-retention safety change) was preserved intact.

## Findings and fixes

1. P1 scoped draft cancel. `app/bot/handlers.py` now emits `cancel:<draft_key>` (not the bare
   `cancel`) and the cancel callback requires an active `collect`/`confirm` state plus a matching
   key. Legacy/stale cancel buttons are answered with an `invalid_request` alert and never clear
   state or mutate the wallet. `/cancel` with no active draft returns a neutral `no_active_draft`
   message; submitted orders (no FSM state) are unaffected. The confirmation keyboard is removed
   best-effort after a successful submit (`edit_reply_markup`).

2. P1 prompt delivery recovery. `ask` now persists a `pending_prompt` marker before every outbound
   question/confirmation/multiple-file prompt and clears it only after the send succeeds. On a
   failed send the next applicable update (text/choice/done/confirm) or the new idempotent
   `/resume` command re-renders without consuming a retried input twice. Accepted inputs are
   persisted before the prompt send and are never rolled back; `submit` idempotency is unchanged.
   The multiple-file `more_files` prompt now renders through the same `ask` path so its failure is
   recoverable too. New localized keys: `resume_none` (and the `/resume` re-render itself).

3. P1 per-owner upload quota. `LocalStorage` gained `quota_bytes`/`quota_files` bounds and enforces
   them in `save` under a POSIX `fcntl` lock (check+write are atomic against concurrent bot/worker
   uploads). An advisory `ensure_quota` pre-check runs in `app/files/telegram.py` before the
   expensive Telegram download. Config gains `STORAGE_QUOTA_BYTES` (50 MiB) and
   `STORAGE_QUOTA_FILES` (100), validated positive. The quota covers abandoned drafts because it is
   counted from the owner's stored files, independent of FSM state. No files referenced by orders
   are deleted; TTL recovery is unchanged. Localized `storage_quota` error in both catalogs.

4. P1 verification-test defects. `tests/test_bounded_fixes.py` no longer indexes
   `inline_keyboard[0][1]` for the single-column cancel button; it locates buttons by callback data
   via a new `button_by_prefix` helper and asserts the keyboard edit. The `Recorder` transport now
   raises `TelegramForbiddenError(method=..., message=...)` and `TelegramBadRequest(method=...,
   message=...)` with both constructor arguments. Added stale-cancel-vs-new-draft and post-submit
   ledger-preservation tests; updated the cancel callback in the existing wallet test to the scoped
   data.

5. P2 low-risk intake/admin polish. Malformed `done:` callback parsing now catches
   ValueError/IndexError (alert instead of crash); negative choice indices are rejected; an empty
   services menu shows a localized `no_services` message; ops admin commands show localized domain
   errors (`unavailable`, `provider_config`, `refund_invalid`, ...) instead of a generic usage
   message; OCR's unreadable-result wording moved to a new `ocr_unclear` key that directs a new
   request instead of a blind resend (the intake `image_unclear` resend wording is unchanged).
   `app/ops/circuit.py` excludes `ocr_unclear` from the circuit breaker like `image_unclear`.

6. P2 notifier slug dedup — decision: NOT A BUG, no change. `app/ops/notifier.py` computes
   `scope = context.get("slug", "global")` and then builds `key = f"alert:{kind}:global"`. The
   README documents "alerts deduplicate by type for 15 minutes", and
   `tests/test_operations.py::test_alert_deduplication_real_redis` asserts one send for eight
   concurrent alerts of the same kind. The `scope` value is still used (as `slug=` in the alert
   message body). The literal `global` in the key is the documented dedup-by-type semantics, so the
   current behavior is intentional.

## Changed files

- app/bot/handlers.py (scoped cancel, prompt recovery, /resume, no_services, parse/choice guards)
- app/bot/ops_handlers.py (localized ops domain errors)
- app/core/settings.py (storage quota settings + validation)
- app/providers/storage.py (per-owner quota + lock; `expire_before` unchanged)
- app/providers/runtime.py (pass quota config to LocalStorage)
- app/files/telegram.py (quota pre-check before download)
- app/ops/circuit.py (exclude `ocr_unclear`)
- app/services/image_to_text/service.py (`ocr_unclear` key)
- app/i18n/ar.json, app/i18n/en.json (`no_services`, `no_active_draft`, `resume_none`,
  `storage_quota`, `ocr_unclear`)
- app/services/image_to_text/test_service.py, tests/test_real_services.py (`ocr_unclear` key)
- tests/test_bounded_fixes.py (constructor fixes, button-by-data, stale-cancel + ledger tests)
- tests/test_draft_recovery.py (new: text/choice/more-files/confirmation recovery + /resume)
- tests/test_storage_quota.py (new: byte/file exhaustion, owner isolation, pre-check, concurrency)
- ENGINEERING/MASTER_ROADMAP.md, AGENTS.md (phase record)

## Verification status

- Tests: NOT RUN. This environment has no `pytest` binary and no `pytest` module
  (`pytest --version` and `python3 -m pytest --version` both fail), so all regression tests are
  authored but unexecuted here. They require the disposable `*_test` PostgreSQL/Redis from
  `tests/conftest.py`.
- Lint/format (`ruff`): NOT RUN (ruff unavailable; general shell denied).
- `git diff --check` (whitespace): PASS over tracked files; the untracked new test/report files
  were reviewed by reading only.
- Static review: PASS (read-only). No migrations, no service-list or core-policy branching, no
  dependency upgrades, no schema changes. Python syntax was not executable-verified in this
  environment.

## Residuals

- The quota lock file is a small per-owner empty file at the storage root (`.quota-<user_id>.lock`)
  and is never cleaned; it is outside the owner glob and not counted against the quota.
- The quota pre-check uses Telegram's `file_size`, which may differ from the processed (e.g.
  re-encoded) size; the authoritative check in `save` still bounds the actual written bytes.
- The `pending_prompt` marker adds one extra FSM write per prompt; acceptable for correctness.
- `/resume` re-renders the current prompt but does not print a separate "resumed" confirmation;
  the re-rendered localized prompt is the response and `resume_none` covers the no-draft case.
- The quota counts all per-owner stored bytes, including worker-saved result artifacts (not just
  customer uploads); the default 50 MiB/100-file bound leaves room above the 5 x 10 MiB upload cap,
  so normal result rendering is unaffected, but a full owner could in principle fail an artifact
  save with `storage_quota` and fail the order.
- The prompt-recovery and quota regression tests could not be executed here, so runtime behavior
  (especially aiogram middleware/exception propagation and POSIX-lock concurrency) is verified
  only by static review.
