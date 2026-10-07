# Real Telegram staging acceptance

Use this guide after hosted tests pass for the source on the staging server. Mocked CI proves
the internal flows; it does not prove Telegram delivery, provider accuracy or actual billing.
Use a dedicated test bot/account and synthetic content. Keep secrets and customer data out of
evidence. Deployment and paid launch are separate decisions.

## Before the journey

Record `git rev-parse HEAD`, deployment method and the hosted workflow link for that source.
Inspect the existing installation before making runtime changes. With an existing Compose setup:

```bash
docker compose ps -a
curl --fail http://127.0.0.1:8000/health
```

Check migration success and API/bot/worker health. For a uv/systemd installation, inspect its
actual units and equivalent health endpoint. Do not start a second polling process for the
same bot. Configure Telegram/admin IDs and AI credentials/rates privately according to README;
never paste `.env` or tokens into a report. AI services remain disabled until the operator enables
them with `/enable SERVICE_SLUG` on this test installation.

## Customer journeys

First send `/start` from the test customer. From the administrator account, use
`/addbalance TEST_USER_ID 50` to issue test credit, then record `/balance TEST_USER_ID`.
The placeholder is the dedicated customer's numeric Telegram ID. This is test credit.

| Case | Customer action | Acceptance |
| --- | --- | --- |
| Echo | Select echo, enter `Acceptance 123`, confirm | Exact text returned; available decreases by the displayed price; reserved returns to zero |
| English UI | Use `/lang`, select English, reopen services/balance | Preference persists after `/start`; menus, prompts and delivery envelope are English |
| Word | Select text-to-office → Word; provide a short report with names, dates and numbers | Opens as editable DOCX; supplied facts and text are preserved |
| Excel | Select text-to-office → Excel; provide a small table | Opens as XLSX; headers and numeric cells are correct; customer formulas remain safe text |
| PowerPoint | Select text-to-pptx; provide a short presentation brief | Opens as editable PPTX; readable slides preserve the provided facts |
| PDF | Select text-to-pdf; provide an Arabic/English report | Opens as PDF; inspect Arabic shaping, mixed text, page breaks and font coverage |
| PDF to Word | Upload a fully text-based sample PDF | DOCX is editable and preserves extracted facts; original layout, images and tables are outside this service |
| Rejected PDF | Upload a blank, encrypted or mixed text/scanned sample | No output file; clear failure; no net credit charge; reserved returns to zero |
| OCR | Try clear Arabic/English images, then an unreadable image | Clear text matches source; unreadable input fails honestly and releases reservation |
| Bottom navigation | Use Services, My orders, Credit, Help and Home during intake | Navigation is not saved as content; draft remains resumable; keyboard has two columns |
| Language during intake | Enter the first field, switch language, then resume | Entered content is preserved; current question and persistent keyboard use the selected language |
| Support during intake | Open support, send a synthetic question, return to draft | Existing draft and prompt index survive; navigation labels are not forwarded to support |
| Order history | Submit two test orders; open My orders and refresh details | Only own orders appear, newest first; current status, original price and Saudi timestamp are correct |
| Confirmation via history | Open a waiting-for-approval order in My orders; approve or reject | Existing order resumes or releases its reservation once; repeated controls cannot settle twice |
| Cancel | Cancel a draft before confirmation | No order charge; old confirmation buttons cannot submit it |
| Confirmation replay | Tap an old confirmation again after completion | No second financial charge; old control is rejected safely |

Inspect each balance using `/balance TEST_USER_ID`. No successful case may capture before
required delivery; no failed case may leave an ordinary customer reservation stranded.
For a provider call of unknown cost, operational budget reconciliation is separate from the
customer's released reservation.

## Recovery and evidence

Use the disposable integration suite for forced transport failure, retries and financial
concurrency. Do not induce failures in production to run this checklist. Any staging restart
test must preserve volumes and use the existing deployment procedure and backup plan.

For each case retain source SHA, timestamp, service slug, order ID, PASS/FAIL/NOT RUN,
file-open result, final available/reserved amounts and sanitized notes. Record actual provider
model/rate assumptions separately; configured cost calculations are not supplier invoices.
Inspect temporary-file cleanup without retaining test document contents in the engineering log.
At-least-once external delivery can duplicate a message across a send/commit crash; settlement
must remain idempotent. Finish with the operational backup/restore checks in OPERATIONS.md.
