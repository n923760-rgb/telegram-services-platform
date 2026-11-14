# Launch preparation — 2026-11-14

## Source and authority

Owner requested completion of existing ready/near-ready services and official bot
operation, then confirmed continuation. Review used canonical
`n923760-rgb/telegram-services-platform` main
`1d0abfc521eb1d6f503ef3255bec25a65d14f65d`, verified against the remote.
Its [hosted workflow](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/43574540880)
completed successfully. Open PR #191 was the only open pull request at inspection,
with head `5231b27c0aaca1bc0e695e79779376727b19a4b9`.

FACT: current registry has 18 customer services: four never require AI, five are
input-dependent, and nine require AI. Historical 16-service/29-case descriptions
are not the current inventory; the acceptance plan currently has 33 cases.
All public plugins declare disabled defaults. This says nothing about the actual
installation's administrator-owned enabled flags, prices or pending orders.

## Completed bounded fix

PR #191 rejects ten line separators in the shared PDF page-selection parser.
Additional lifecycle tests found that the parser fix alone is insufficient:
`StrictModel` strips boundary VT/FF/NEL before its after-validator calls the parser.
An extraction/rotation request can therefore still create an order and reserve
test credit. Six of twelve new lifecycle cases reproduced this on the partial fix.

Validate raw `pages` with the shared parser before Pydantic normalization. Retain
ordinary boundary spaces/tabs, Arabic digits/commas, explicit page order, ranges,
the 200-page bound and existing error handling. Invalid input now creates no
order/job/provider hold/usage and no ledger entry beyond the original test seed.
No schema declaration/version, dependency, migration, administrator setting,
price, payment policy or production data changes are required.

## Verification

PASS on the combined application tree:

- 92 focused PDF parser/plugin/lifecycle checks, plus 15 unittest subtests.
  Includes the twelve new pre-reservation cases, capture/replay, failure release,
  unsupported PDF features, cleanup, old prepared outputs and admin overrides.
- 498 selected architecture, foundation/recovery, Stars, activation, draft,
  provider-contract, text editing/summary/translation, card and QR checks.
  Provider and Telegram interactions in these regression tests are synthetic.
- Whole-repository Ruff lint/format and whitespace checks.
- Alembic upgrade and drift check against disposable PostgreSQL/Redis.
- Isolated native acceptance: 10 PASS cases across eight services, zero provider
  calls/cost, zero active orders and zero reserved halalas after the run.
  Cases: `csv`, `images_pdf`, `tables_direct`, `pdf_extract`, `pdf_rotate`,
  `pdf_merge`, `word_direct`, `text_pdf_direct`, `business_card`, `qr_sheet`.
- Rendered and inspected the nine synthetic PDF output pages, plus separate fixed
  Arabic card/QR/direct-PDF builder samples. Arabic QR decoded to its exact source
  URL. These samples do not qualify Microsoft Office, mobile or arbitrary content.

LIMITS: full local suite was not completed. An initial exploratory run lacked
LibreOffice; attempts to provision the full worker encountered the Cloud machine's
limited disk and Docker VFS copying overhead. Temporary build/image resources were
removed. Final successful checks above ran after space recovery against disposable
data. Native acceptance ran the actual application job/ledger/storage pipeline on
the host, with its file delivery adapter; it did not send files through Telegram.
This is not a successful production Docker build or a real provider/payment test.
Hosted verification of the updated PR remains a separate source-bound gate.

## Service decision matrix

These are release priorities, not assertions that the production bot is enabled.
PASS means the named synthetic mode passed here; omitted modes remain unqualified.

| Priority | Service / source version | Evidence this round | Remaining launch work |
| --- | --- | --- | --- |
| First cohort | `pdf_tools` v5 | Native merge/extract/rotate PASS; completed raw-input fix | Candidate CI, real Telegram files and target PDF viewer |
| First cohort | `images_to_pdf` v3 | Ordered native pages PASS | Representative uploads and mobile output review |
| First cohort | `csv_review` v4 | Native XLSX review PASS | Representative Arabic/English CSV; native Excel edit/save/reopen |
| First cohort | `qr_codes` v2 | Native PDF PASS; fixed Arabic exact-URL decode PASS | Target phone scan and Telegram delivery |
| Next, direct path | `interactive_card` v2 | Direct native PDF PASS; fixed Arabic rendering inspected | Links/phone on target phone; smart AR/EN modes need real provider review |
| Next, direct path | `text_to_office` v9 | Literal Word PASS | Native Word review; smart Word/Excel need real provider and source reconciliation |
| Next, direct path | `text_to_pdf` v8 | Direct PDF PASS; fixed Arabic rendering inspected | Target viewer; smart mode needs real provider qualification |
| Next, direct path | `pdf_tables_excel` v7 | Direct table XLSX PASS | Difficult text PDFs and native Excel; proposed labels need AI review |
| Further qualification | `text_to_word_pdf` v5 | Not executed in native acceptance here | LibreOffice worker and real Arabic/English Word/PDF review |
| Further qualification | `text_editing` v3 | Synthetic schema/lifecycle regressions PASS | Real corrections/rewrites preserving meaning, negation, values and contacts |
| Further qualification | `text_summary` v3 | Synthetic schema/lifecycle regressions PASS | Real source-supported summaries; check omitted conditions |
| Further qualification | `text_translation` v2 | Synthetic schema/lifecycle regressions PASS | Real AR/EN meaning, negation and source-fact review |
| Further qualification | `image_to_text` v7 | Source/hosted baseline reviewed; no live extraction here | Clear/difficult AR/EN/mixed images; literal chat and TXT download |
| Further qualification | `document_image_enhancement` v4 | No live quality qualification here | Real source comparison and measurable useful improvement |
| Further qualification | `cv_formatting` v7 | No live/native qualification here | Dense/bilingual CV, supplied facts only, native Word/PDF |
| Further qualification | `meeting_minutes` v4 | No live/native qualification here | Arabic/English notes, uncertainty, decisions, assignees and deadlines |
| Further qualification | `text_to_pptx` v8 | No live/native qualification here | Long Arabic content, literal restrictions and every slide in PowerPoint |
| Further qualification | `pdf_to_word` v9 | No live/native qualification here | Text-only PDFs, editable tables/reading order and source fidelity |

`hosted_profile` and `echo` are administrator-only; `local_ocr` is retired in
favor of `image_to_text`. They are not additional launch products. Do not add new
business/teaching plugins before finishing the selected launch cohort.

## Operational handoff and remaining blockers

UNKNOWN: deployment machine/method, deployed SHA, bot identity, current service
flags/prices, provider configuration/rates/budgets, purchase terms and runtime
payment/refund evidence. No production credentials or server connection were
available to this review. Never copy tokens into the report, repository or chat.

1. Pass updated source CI. Identify the existing installation and use its approved
   deployment procedure; inspect current version, active orders, worker native
   capabilities and read-only `python -m app.ops.service_portfolio` output first.
   Do not use `--enable` as a quality check or blindly enable the whole portfolio.
2. Retain/rehearse database and off-server backup/restore. Verify worker/API/bot
   compatibility and dispatch/delivery recovery before updating versioned work.
3. Rebuild and source-verify the actual worker. Run the selected source-bound
   acceptance cases and inspect outputs on the intended customer apps. Direct
   Word/PDF retains the documented explicit literal request; do not advertise
   successful native direct cases as successful AI modes.
4. Complete dedicated Telegram staging journeys: upload, confirmation, delivery,
   duplicate events, failure/cancellation, recovery and cleanup. Real users and
   customer production balances are not synthetic test subjects.
5. For paid launch, privately configure owner-approved independent Stars prices,
   bilingual terms and support, authenticated webhook and dedicated test-server
   purchase/refund/reconciliation journeys. SAR wallet balances remain test credit.
   Mocked Stars regressions above do not satisfy real payment acceptance.
6. Enable only services whose gates passed, then inspect logs/support/cost reports.
   Add the next cohort after actual provider and native/mobile qualification.

No main merge, production deployment, live provider calls, real Telegram messages,
Stars charges/refunds or production service activation were performed in this review.
