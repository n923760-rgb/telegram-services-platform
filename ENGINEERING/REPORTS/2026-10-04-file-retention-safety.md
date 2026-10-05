# File retention safety review

Date: 2026-10-04. Task branch: ai/task-20261004-182433.
Starting HEAD: b2f8699 "Fix Compose configuration validation in CI".
Scope: file retention safety only, plus regression tests and this factual record.
No commits, pushes, merges, releases or production database access were performed.

## Findings fixed

1. Age purge destroyed retry references. `app/files/retention.py::cleanup` cleared
   `order.inputs` and `order.result` for every terminal order older than the TTL and then ran
   a storage-level age expiry, even when `files_deleted=False`. A terminal order whose durable
   deletion had failed lost the keys needed to retry deletion, and its files were still age-expired.
   Fix: purge references only for terminal orders with `files_deleted=True`; pending-deletion
   orders keep their references.

2. Age-only expiry deleted referenced files. `LocalStorage.expire_before` removed any customer
   file older than the TTL without knowing which orders still needed it, so live inputs and
   prepared artifacts (and pending terminal-deletion files) could be removed.
   Fix: `expire_before` now accepts a `keep` set; `cleanup` builds that set from every order whose
   `files_deleted=False` (live orders and pending terminal deletion) and skips those keys.
   Truly abandoned uploads (referenced by no order) still expire by age.

3. Protection failed open on malformed payloads. Caught during this implementation review
   (independent reviewer), not the original baseline. Key extraction silently skipped a malformed
   input schema or malformed result artifacts, so `keep` could be incomplete and age expiry would
   delete a still-referenced file. Fix: extraction errors propagate; `_referenced_keys` does not
   suppress them and `artifact_keys` validates the result/artifacts/item shape, raising instead of
   omitting. One malformed order therefore aborts the age-expiry sweep (fail closed).

## Changed files

- app/providers/storage.py: `Storage.expire_before` signature gains `keep`; `LocalStorage`
  skips keys present in `keep` by matching the path relative to the storage root.
- app/files/retention.py: extracted `input_keys`/`artifact_keys`/`_referenced_keys`; `cleanup`
  gates reference purge on `files_deleted=True` and passes protected keys to `expire_before`;
  `delete_inputs` reuses `input_keys`; `artifact_keys` validates shape and fails closed; shared
  `TERMINAL` literals reused where touched.
- tests/test_retention.py: seven regression tests (failed deletion + retry preserves input and
  result references then purges only after durable deletion; aged active input survives; aged
  prepared artifact survives; abandoned upload expires; successful terminal purge clears
  references; malformed input schema fails closed; malformed artifact result fails closed).

## Concurrency reasoning

The protection is a snapshot of referenced keys read before `expire_before`, not a lock, so this
is NOT claimed race-free. Practical safety holds because: (a) a newly submitted order references a
freshly uploaded file whose mtime is well after the TTL cutoff, so age expiry cannot remove it in
the same sweep; (b) terminal orders never transition back to active states; (c) a concurrent
`cleanup_terminal_files`/job-finish that flips `files_deleted=True` only marks files already
deleted, so a stale key in `keep` is harmless. A crash or an order stuck in a nonterminal state
longer than the TTL is protected because `files_deleted` remains false and its keys stay in `keep`.
This is a snapshot-conditioned, best-effort protection: a malformed referenced payload is never
silently bypassed, but the sweep does not hold locks across the snapshot and the filesystem walk.

## Fail-closed availability tradeoff

Because extraction errors now abort the sweep, a single malformed order (input schema or result
artifacts) blocks age expiry — including orphan expiry — until an operator repairs the row. This
trades availability for safety: files are never age-deleted when complete protection could not be
established. Orphan expiry is therefore NOT guaranteed in a sweep that encounters malformed data;
it only runs in a fully readable sweep.

## Verification status

- Tests: NOT RUN. This environment has no installed Python dependencies and no pytest binary;
  `pytest` and `python3 -m pytest` both fail, `uv run pytest`/`uv sync` are outside the permitted
  command set, and dependency installation requires approval not granted. The seven regression
  tests are authored but unexecuted here.
- Lint/format: NOT RUN (ruff unavailable; general shell denied).
- Tracked-diff whitespace (`git diff --check`): PASS. The untracked test file and report are not
  covered by `git diff --check` and were reviewed by reading only.
- Independent final reviewer static approval: PASS (static review only). The reviewer approved the
  fail-closed extraction, the `files_deleted=True` age-gate, and the test-only `updated_at`
  re-aging correction (which made the purge assertion independent of the `onupdate` mechanism).
  Runtime execution of tests remains NOT RUN.

## Unresolved findings (out of scope, not addressed here)

- Group privacy: `app/bot/middleware.py`, `app/bot/handlers.py`, `app/bot/ops_handlers.py` do not
  gate incoming messages on a private chat, so group messages can reach customer flows.
- Cancel semantics: `app/bot/handlers.py` cancel clears the FSM state but does not persist the
  order change and leaves stale inline buttons.
- Support failures: `app/bot/ops_handlers.py` commits the ticket before sending admin
  notifications, so a send exception loses the confirmation path.
- Stale admin service: `app/ops/admin.py` `set_service` indexes `registry.types[slug]`, raising an
  unhandled `KeyError` when enabling a DB row whose plugin was removed.
- Cost-cap labels: `app/ops/costs.py` mislabels user/global cost-cap keys.
- AI endpoint: `app/core/settings.py` permits `http` as well as `https` for `ai_base_url`.

These remain open and were not changed by this file-retention work.
