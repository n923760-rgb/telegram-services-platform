# Service readiness and improvement order

The owner prioritizes complete, professional service outputs before paid launch.
Keep one customer catalog derived from registered plugins; retain existing service
identities, orders and meaningful output choices. Do not add another customer-facing
quality mode or expose internal provider/qualification controls in the Mini App.

## Operational report

The existing isolated acceptance command writes `results/report.json`. Its new
`service_readiness` section groups all public services by their registered category,
including services omitted from a selected run. It is refreshed after each case,
so an interrupted run retains honest progress. The plan command also shows all
services as untested, without database writes or provider calls.

| Automated status | Meaning | Next action |
| --- | --- | --- |
| NOT_RUN | None of this service's planned cases ran | Run its missing cases in isolation |
| INCOMPLETE | Some cases passed; other modes were not run | Test remaining modes before accepting the service |
| FAIL | At least one case failed, even if other modes passed | Fix and rerun the failing cases |
| PASS | All this service's cases passed in this run | Review source fidelity, appearance and the target viewer |

The report lists passed/failed/not-run case names, service version and specific
manual review checks from the fixtures. Manual review stays `NOT_RECORDED` and
launch status stays `NOT_ASSESSED`: no automatic PASS authorizes paid launch.
Results from older runs are not silently combined; a successful selected run
can still have incomplete services in the portfolio report. Inspect the existing
top-level financial/run status as well; per-service results do not override it.

The results ZIP includes `source-commit.txt` from the clean host checkout.
This is checkout provenance, **not** proof of the source used to build the worker.
Rebuild the worker from the intended source before isolated acceptance, following
the existing operations procedure. Mounted acceptance scripts alone do not update
builders, plugins or providers. Keep application/version and image provenance with
manual evidence. Old archives without the new section remain historical evidence.

## Priority order

| Priority / category | Services | Required outcome before acceptance |
| --- | --- | --- |
| 1 / Documents | text_to_office, text_to_word_pdf, text_to_pdf, text_to_pptx | Professional structure; editable Office objects; source facts and language retained; long Arabic/English/mixed content; no clipping. Check dated contacts and native edit/save/reopen in the intended Office app. |
| 2 / Data | csv_review, pdf_tables_excel | Reconcile every record and value; preserve IDs/leading zeros/duplicates; distinguish blank from zero; safe formula-like text; readable native sheets. |
| 3 / PDF and images | pdf_tools, images_to_pdf, pdf_to_word, image_to_text, document_image_enhancement | Correct pages/order/rotation; source pixel/content fidelity; honest text-only conversion limits; difficult scans fail clearly; enhancement must show meaningful improvement. |
| 4 / Professional | cv_formatting, meeting_minutes | Dense/multipage and bilingual CVs; no invented credentials. Minutes preserve decisions, uncertainty, owners and deadlines without inventing commitments. |
| 5 / Text | text_editing, text_summary, text_translation | Demonstrate real corrections/rewrites and cross-language translation; preserve negation/numbers/contacts; summary points supported by source references. |

For each service: fix observed failures, run all planned modes, compare source and
output, inspect every page/sheet/slide, then test Telegram delivery and the target
viewer using a dedicated staging customer. Record PASS/FAIL/NOT RUN and the tested
source, engine and app version. Use [output quality gates](OUTPUT_QUALITY.md) and
[Telegram acceptance](TELEGRAM_ACCEPTANCE.md) for detailed criteria. Historical
configuration checks, HTTP health and mocked tests do not substitute for this work.

Known Word literal/Calc numeric-leading-email viewer failures remain documented in
OUTPUT_QUALITY.md. This reporting change does not resolve or waive them. No service
enablement, pricing, payment mode, provider budgets or production data changes are
part of this round.
