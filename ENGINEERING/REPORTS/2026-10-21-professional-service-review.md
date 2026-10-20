# Professional service review and AI value policy

Date: 2026-10-21 (Asia/Riyadh). Baseline: official main `3af2a5a4e788ef2295b04008ad832bacf68ba6c6`.
Owner requests reviewing the remaining services, professional paid value and permission to
use AI where it improves the result. This explicitly supersedes a preference to avoid AI
when avoidance would reduce useful output quality. It does not remove source fidelity,
consent to change wording, ownership, per-job cost admission or bounded correction.

## Source findings

FACT: The 16 public services have nine required-AI contracts, four conditional-AI contracts
and three deterministic contracts. Production `runtime_for` enables content review whenever
AI is needed. Processing stays internal to the purchased service; no new engine-selection
screen is needed. Existing preserve/improve choices express consent to change content.

FACT: The shared review checks meaning, coverage, names, numbers and language, but had no
fixed finding for identifiable fluency, grammar or requested-register defects. Editing and
translation creation prompts describe their tasks; the review contract did not explicitly
separate paid prose quality from fidelity or exempt already-correct/literal source content.

CHANGE: Add fixed `quality` finding and explicit task-sensitive review guidance. Reviewers
can request the existing one correction for identifiable poor grammar, unnatural translation,
incoherence or incompatible requested tone. Proofreading retains wording/register; correct
text can remain unchanged. Literal OCR, tables, source quotes and identifiers are not prose
rewriting tasks. Clarify AR/EN translation styles and proofreading/rewriting expectations.
No additional provider calls or retry allowance; new prompt/schema input is charged through
the existing per-call upper bound before dispatch. No changes to public schemas, versions,
prices, service activation, production provider pause, limits or cached-result replay.

## Per-service value and acceptance matrix

These are source contracts and required evidence, not blanket live PASS statements.

| Service | AI use | Professional-value acceptance |
| --- | --- | --- |
| `cv_formatting` | Required | Complete AR/EN/bilingual editable CV and PDF; actual career facts, no invented seniority/metrics; readable sections and complete second language on a fresh page. Inspect real layout and transliteration. |
| `text_to_pptx` | Required | Requested slide count, useful narrative, editable native text/tables, readable spacing; correct source facts and contextual numbers. Inspect every slide and mobile appearance. |
| `text_to_office` | Conditional | Smart Word and Excel planning use AI. Direct Word preserves text. Excel keeps source rows, literal IDs/precision and traceable references; no invented formulas/totals. Native Office must open/edit/save/reopen. |
| `text_to_pdf` | Conditional | Preserve supplied text or explicitly improve wording/organization; correct Arabic direction/date order, complete source facts, readable page flow. Render all pages. |
| `text_to_word_pdf` | Conditional | Chosen Word/PDF/both, same approved content, professional layout, clear preserve/improve consent; inspect pair consistency, tables and pagination. |
| `pdf_to_word` | Required | Useful editable extraction within its text-only scope; preserve source details. Reject images/forms/unsupported input rather than promise original layout. Retest sparse-table source after pending #120. |
| `image_to_text` | Required | Native recognition plus source review/fallback; preserve mixed-language text and long-output whitespace. No invented unclear characters or rewriting; inspect actual photos and source detail. |
| `document_image_enhancement` | Required | Native image candidates plus source-based AI selection; meaningful illumination/legibility improvement with all marks and color distinctions retained. Decline uncertain/no improvement; pending #120 needs live retest. |
| `meeting_minutes` | Required | Every note represented, correct discussion/decision/action/review classification, exact assigned owner/deadline, customer structure confirmation, useful action register. Never turn proposals into decisions. |
| `pdf_tables_excel` | Conditional | Native extraction retains literal cells/source rows. AI may propose headings, with explicit review. Preserve source headers/references; ambiguous table boundaries need representative acceptance. |
| `text_translation` | Required | Complete natural AR/EN in requested style; same actors, negations, conditions, obligations, names and literal numeric/contact values. Formal and casual are meaningful choices. |
| `text_editing` | Required | Proofreading corrects errors with minimal changes; rewriting improves clarity/tone. No invented commitments; clean result plus exact original/change report. |
| `text_summary` | Required | Concise useful source-cited points with decisions, deadlines and conditions; actual compression without wrong approval or hidden omissions. Full normalized source retained in report. |
| `csv_review` | Deterministic | Editable Data/Source/Review/Columns, literal IDs/zeros/blanks/formula-looking values, exact disclosed counts. Similarities are bounded lexical suggestions; no automatic row deletion/merge. |
| `images_to_pdf` | Deterministic | Complete chosen page sequence, readable A4 fit and retained received pixels; inspect orientation and every page. AI is unnecessary for copying these images. |
| `pdf_tools` | Deterministic | Correct merge/extract/rotate sequence and geometry, retained native pages, rejected unsupported forms. Pending #121 adds empty declarations/orphan Widget boundary; AI adds no value to these operations. |

## Validation and remaining gates

Local service tests use synthetic inputs and injected/scripted providers. They prove
contracts, orchestration, builders and failure handling, not real model judgement.
New AR/EN editing/translation scenarios deliberately retain numeric tokens while exercising
quality rejection, one correction, accepted/failed review, deferred file generation and
unchanged correct text. PostgreSQL cases check single capture/release, actual per-call cost,
cleanup and cached delivery without regeneration. They require hosted execution where the
local DB/native-export tools are unavailable; record results in the canonical roadmap.

UNKNOWN here: current server HEAD/health and provider pause, actual current administration
prices, and current real-provider/mobile quality for every service. Source-level permission
to use AI is established; it does not automatically clear an operational provider pause.
No access to production or live provider credentials was used in this review.

Next live qualification uses the existing isolated `service_acceptance` runner and its exact
source-bound results. Retest #120 PDF conversion/enhancement, then all 29 existing portfolio
cases and representative long/mixed/ambiguous sources. Inspect actual content and files in
Office/on the phone against the above matrix. Valid JSON, token matching, health and a model's
approval alone cannot certify professional content, file appearance or paid value.

Keep document-entry consolidation and general intake review/edit UX as separate bounded
rounds. Their overlap and commercial prices need explicit product handling; do not silently
move accepted historical orders or change prices as part of this quality review.

## Observed local results

- PASS: 35 focused gateway/professional-quality tests, including 15 new cases.
- Broader invocation: 505 PASS; five FAIL_ENV due to missing LibreOffice, independently
  rerun with `document_render_unavailable`; 41 ERROR_ENV from the unrelated PostgreSQL
  autouse fixture. Do not report the overall invocation as passed.
- PASS: all 41 existing pure Excel/PPTX builder tests in an isolated DB-free harness;
  test bodies are unchanged. They validate native structure/readback, not human visual approval.
- PASS: source inventory, three direct architecture gates, lint, format and diff checks.
- NOT RUN: twelve new PostgreSQL lifecycle scenarios (collection PASS), full hosted suite,
  worker container qualification, live provider and customer phone/Office acceptance.
- Test counts overlap. No local credentials, actual customer input or billable calls used.
