# Generic input editing before purchase — 2026-10-21

## Source and scope

FACT: main `05f4ebb14c16953455033d063a286aad77bc9a2b` provides a localized input
summary, but customers still have to cancel and start again to change an input.
Owner authorizes continuation of the latest review. This bounded round adds editing
of unsubmitted draft inputs; provider qualification and open service-quality branches
remain separate. No production deployment is performed.

## Behavior and boundaries

- The existing confirmation gains an Edit inputs control. Its menu lists only active
  schema fields using the shared localized review labels, without customer content.
- Read owner-bound durable admission before showing/selecting edit fields. Any existing
  order with that purchase key blocks editing, including an awaiting-payment order whose
  invoice/FSM notification failed. A failed acceptance read leaves the draft untouched.
- Selecting a field rotates the purchase key before prompting. Previously issued
  confirmation/edit/cancel buttons cannot submit or mutate the revised draft.
- Preserve unrelated source text, uploads, explicit selections and omitted optional fields.
  Recollect the selected input plus its transitive `when` dependencies. Hidden dependent
  values are removed; future dependency questions remain queued until their parent has
  been answered, rather than being discarded while the parent is temporarily absent.
- Reuse existing text validation, choices, skip, upload and Done handlers. Optional title
  removal and multi-upload replacement follow the same generic path as initial intake.
- Return without changes restores the original input snapshot and rotates the key again.
  The snapshot is transient FSM data under the existing draft TTL, removed on completion
  or ordinary draft cancellation. Unreferenced old/replacement uploads use existing age
  expiry; editing does not synchronously delete bytes or extend retention guarantees.
- Persist pending-prompt state before outbound sends. Failed edit, review or restore sends
  recover the intended screen without applying the next message as a replacement input.
- Preserve original service/version/price, currency and full terms. Editing never calls
  submit, creates an invoice/order, reserves credit or invokes a provider. Final admission
  still validates ownership, service/cross-field inputs, price/version, availability and
  financial policy. Cross-field relationships not declared by schema `when` stay subject
  to that final validation; no service-specific guesses about dependencies were added.

## Verification

PASS locally: 107 focused tests, including 34 new handler/helper edit cases, plus existing
review, intake alias, content-mode, document-output and availability checks. Cover both
languages/payment modes, preserved content, conditional/transitive/nested fields, invalid
or stale callbacks, optional-field clearing, upload Done/restore and send-failure recovery.
Three architecture gates run directly; global lint/format and whitespace checks pass.

NOT RUN locally: eight new PostgreSQL/actual-dispatcher cases, collected successfully.
They require zero orders/reserved credit during editing and stale confirmation, then one
purchase with the revised/original-restored input and a single reservation on repeated
confirmation. Additional crash-window cases block editing after durable admission, and
failed Stars invoice delivery must retry the same order/checkout with zero SAR reservation. Full hosted workflow must pass before merge. Local PostgreSQL is unavailable.

NOT RUN: real Telegram delivery, provider judgement, native mobile Office output, live
Stars purchase/refund or server rollout. This round completes the general editing path
alongside #125's review summary; early mixed-mode availability and all-service professional
output acceptance remain separate review priorities.
