# Operations

Run `scripts/backup.sh` daily from the project directory, for example a root cron entry:
`15 2 * * * cd /srv/telegram-services && ./scripts/backup.sh >> /var/log/services-backup.log 2>&1`.
The script uses pg_dump custom format, restrictive permissions, atomic rename and 7-day retention.
Use an SSH key to copy each completed dump to a separate server, for example
`rsync -a --chmod=F600 backups/ backup-user@backup-host:/srv/backups/telegram-services/`.
Check copy exit status, alert externally on failure, and keep a separate remote retention policy.
Keep a separate encrypted copy of .env and any files that must survive a server loss.

Restore into an empty replacement database, never blindly over production:
1. Stop bot, worker, API, monitor; retain the original database/volume.
2. Point .env and Compose at a NEW empty PostgreSQL database/volume.
3. Verify target and backup, then `CONFIRM_RESTORE=YES ./scripts/restore.sh backups/FILE.dump`.
4. Run migrations, compare ledger/order counts and totals, and test a single isolated order.
5. Restart services. Reconcile uncertain provider costs and interrupted deliveries.
Test the restore periodically on a disposable instance. Customer-file volume is separate from pg_dump.

The independent monitor can report worker/Redis/database failures while the worker is down.
It cannot alert when the VPS or its internet connection is down: use an external uptime monitor.
Alerts deduplicate for 15 minutes through Redis, with shared-volume lock fallback.
A send outage may postpone alerts. No secrets or customer content is included in alerts.

Cost settings use Settings rows with JSON {"value": VALUE}, overriding corresponding environment defaults.
Daily boundaries and report cron use Asia/Riyadh. Cost reservations cover in-flight exposure;
uncertain provider calls retain exposure until billing reconciliation (no invented zero-cost success).
Assign provider costs to the cost hold's opening day, matching admission budgets rather than
the later settlement day. Reports show unsettled exposure separately; margin remains provisional.
A report sent before midnight is a snapshot of that day, not a closed accounting statement.
PROVIDER_BALANCE_SAR is optional operator-reported balance; providers without a balance API remain unknown.
MAX_JOB_COST_SAR, MAX_DAILY_COST_SAR and MAX_COST_PER_USER_PER_DAY must be positive decimals.
Disabling a service cancels all unsettled orders and releases reservations, including pending deliveries.
A concurrent Telegram send may already have reached the customer; cancellation never captures their credit.
Re-enabling resets the breaker observation window.
Re-enable with /enable SLUG. Support admins reply with /reply TICKET_UUID MESSAGE.
Delivery is at least once: a crash after Telegram accepts a send but before DB commit can duplicate a
message/file, while ledger settlement and refunds remain idempotent. Never claim exactly-once sends.


Provider cost is computed from returned usage and the configured model rates and exchange rate.
It is not an invoice receipt: discounts, cached-token rates and subsequent billing adjustments are not
inferred. Configure conservative current prices and reconcile discrepancies against provider billing.
A timed-out call might have been billed: inspect cost_holds and provider records, then run
`uv run python -m app.ops.reconcile HOLD_UUID CONFIRMED_COST_SAR`. This is an operator action, not
an automatic release of unknown exposure. The reconciliation command is idempotent for equal amounts.

The circuit breaker evaluates the most recent configured window of completed/failed jobs, after the
minimum sample count, and also alerts on consecutive failures. User credit releases are not a refund
of provider expenditure: OCR rejected as unreadable still may incur provider cost.


Revised-spec controls:
- Jobs record terminal finished_at; reports and circuit windows use outcome time, not later content edits.
- Cancellation is distinct from execution failure; missing/unreadable input and budget/config gates do not trip the service breaker.
- Usage rows preserve provider/model and non-secret rate assumptions. Historic unknown pricing remains unknown.
- Daily reports retain pending Redis work and retry every minute after failed sends. Crash windows can still duplicate an external send.
- Financial operations lock customer rows before order/job rows. Provider-budget operations lock global budget, user budget, then job.
- Retry helpers apply only to PostgreSQL deadlock/serialization aborts in database-only functions, at most three attempts. Never decorate AI or delivery calls.
- Ledger keys are globally bound to the original customer and payload. Migration 0009 aborts if historic keys conflict; inspect conflicts and propose a reviewed resolution, never rewrite immutable history automatically.
- Banning blocks new orders and structure approvals. Existing queued/running orders continue; waiting approvals expire and release credit.


Terminal file deletion has a durable files_deleted marker and a 20-second/startup recovery sweep.
Cleanup failures keep the marker pending. Storage implementations own TTL expiry; Telegram delivery
reads through the storage interface rather than assuming a local filesystem path.
