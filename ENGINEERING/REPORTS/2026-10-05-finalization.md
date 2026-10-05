# Finalization round: recovery notice, truthful quota/stale/confirm wording, quota docs

Date: 2026-10-05. Task branch: ai/task-20261004-182433.
Starting HEAD: b2f8699 "Fix Compose configuration validation in CI" (unchanged; no commits made).
Scope: smallest approved corrections to existing uncommitted work only. No commits, pushes, merges,
releases, secret changes or production database access were performed. All prior uncommitted work
(bounded fixes, file-retention safety, draft recovery, upload quota) was preserved intact.

## Git evidence

- `git status` shows uncommitted work across the existing files plus this round's edits and one new
  report. No commits, no staging, no remote mutations.
- `git diff --check` over tracked files: PASS (no whitespace errors).
- Tests/lint: NOT RUN. `pytest --version` fails (`pytest: command not found`) and
  `python3 -m pytest --version` fails (`No module named pytest`). No pytest binary or module is
  installed in this environment, and the disposable `*_test` PostgreSQL/Redis dependencies are not
  reachable, so every regression test authored across all rounds remains unexecuted here.

## Changes applied

1. P1 explicit recovery notice for a not-applied update. `app/bot/handlers.py::_resume_if_pending`
   now sends a localized `update_not_applied` notice before re-rendering the pending prompt, so a
   new image B arriving after A's `more_files` acknowledgement failed is not silently dropped and
   the `more_files` text ("File received") is no longer read as confirming B. No-consumption and
   idempotence are unchanged: the triggering update is never consumed, and if the re-render send
   itself fails `ask` leaves `pending_prompt` set, keeping the draft recoverable.

2. P1 truthful storage-quota wording. `storage_quota` (ar/en) no longer instructs the user to
   "complete or cancel" drafts to free space (cancellation does not free files immediately). It now
   states files are cleaned up automatically and directs the user to try again later, with no
   credit charged and no unsafe deletion.

3. P1 dedicated stale-button guidance. A new `stale_button` key (ar/en) directs the user to the
   latest controls or `/resume` and does not assert a draft exists. It is used for stale/mismatched
   cancel, choice, skip, done and confirm callbacks and the catch-all expired-callback handler.
   Genuinely invalid inputs (malformed callback data, out-of-range/negative choice index) keep the
   generic `invalid_request` message.

4. P1 confirm-state instruction. `app/bot/handlers.py::confirm_prompt` now answers a localized
   `confirm_unchanged` instruction when a delivered confirmation receives non-command text (input
   unchanged; use Confirm or Cancel; no implicit edit or submit). Pending re-renders still use the
   recovery notice path and never consume the text.

5. Bounded documentation. Added nonsecret `STORAGE_QUOTA_BYTES=52428800` and
   `STORAGE_QUOTA_FILES=100` defaults to `.env.example` and a README environment-table row (no
   `.env` was touched). Corrected the misreported lock filename in
   `REPORTS/2026-10-04-full-review.md` to `.quota-<user_id>.lock` and the `STORAGE_QUOTA_BYTES`
   size to 50 MiB. Updated AGENTS.md phase record and MASTER_ROADMAP.md with third-round coverage
   and this finalization round.

## Authored tests vs BLOCKED execution

Authored (not executed):

- tests/test_draft_recovery.py (new): `test_new_image_after_failed_more_files_is_not_applied`
  (distinct image B not accepted; `update_not_applied` notice shown; only A retained) and
  `test_stale_cancel_preserves_draft_and_resume_restores` (stale cancel answered with
  `stale_button`, newer draft survives, `/resume` re-renders it).
- tests/test_draft_recovery.py (assertions strengthened): `update_not_applied` notice asserted in
  `test_failed_confirmation_prompt_recovers_and_submits_once`; `confirm_unchanged` asserted in
  `test_delivered_confirm_ignores_text_and_keeps_commands`.
- tests/test_bounded_fixes.py (assertions updated): three stale-button paths now expect
  `stale_button` instead of `invalid_request` (stale confirm after cancel, stale cancel vs new
  draft, post-submit stale cancel).

Execution: BLOCKED. No pytest binary/module; `python3 -m pytest` exits with `No module named
pytest`. These were not run here and are not reported as PASS.

## Residual risks (unchanged; retained as limitations, no scope expansion)

- Per-owner quota pre-check uses Telegram's `file_size`, which may differ from the processed size;
  the authoritative check inside `save` still bounds the written bytes.
- The quota lock file is a persistent per-owner empty file at the storage root and is never
  cleaned; it is outside the owner glob and not counted against the quota.
- Stale draft buttons from a `/cancel` command (not the inline button) are neutralized by state
  filters and the `stale_button`/`expired_callback` fallback, not by removing their keyboards.
- The `pending_prompt` marker adds one extra FSM write per prompt; accepted for correctness.
- The recovery-notice, stale-button and confirm-state behaviors could not be executed here, so
  aiogram middleware/exception propagation and FSM routing are verified only by static review.

Historic NOT RUN records were left as NOT RUN (not revised to PASS), and no cache/hosted evidence
was inferred.
