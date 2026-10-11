# One outcome, internal implementation selection

## Authority and baseline

Owner requests one extraction service, no local/AI engine choice, and the same
principle across current/future services. Baseline main 7a7c5c2 / PR #47.
Payment completion remains last. No production deployment or activation performed here.

## Implementation

- Canonical image_to_text v4 is named Extract text from images. Images-only intake;
  native mixed-language recognition first, accept only nonempty confidence >=0.90,
  retaining the native numeric-word >=85 and mean >=0.70 rejection safeguards.
  Classified unclear/unavailable native results or a native payload over its 20MB
  aggregate bound use the existing injected job-scoped AI. Busy/timeout/limits,
  invalid files, ownership errors and unknown failures do not authorize fallback.
  AI still validates readable/confidence >=0.70/nonempty; no translation/rewrite.
- Conservative AI admission/configuration gate remains, even if native recognition
  succeeds. Actual AI exposure/usage is recorded only when called. One order,
  existing price/reserve/capture/release and normal cached delivery; no extra fee.
- Plugin-owned replaced_by metadata retires local_ocr from customer menus and new
  purchases. Legacy button starts a fresh canonical draft at its CURRENT price;
  disabled/unpriced canonical target remains unavailable. No fallback to the old
  lower price and no automatic activation. Historical plugin remains executable;
  idempotent old purchases replay before new-admission checks. Existing admin DB
  overrides/history are preserved; re-enabling a retired plugin is rejected.
- PDF tables v2 removes customer method input. Internally try lattice, then stream
  only for missing/quality failure (maximum two bounded native calls). No retry on
  unsafe/resource failures, guessing, mixing or inventing cells. Existing complete
  source-bound review/confirmation stays; old v1 work follows normal version
  cancellation/release. A passing extractor metric is not proof of all cell accuracy.
- Generic registry validates direct existing canonical replacements, forbids self,
  missing targets/chains; followups cannot target retired products. Generic core
  admission/callback/catalog metadata, no named service branch in policy layers.

## Current service audit and future policy

All 18 registered plugins reviewed. Only the OCR pair is duplicate same-outcome
implementation. Keep historical local_ocr internally, not a second product.
PDF table algorithms are internal. Document direct/smart and table heading options
are labeled by the resulting content, not AI/no-AI: Preserve text / Organize content,
Generic columns / Suggest headings. Meaningful consent is not removed.

Keep output-format choices (Office/PDF/Word-PDF/PPTX, image-PDF orientation), operations
(PDF merge/extract), source CSV delimiter/whitespace and optional similarity report,
editing proofread/rewrite/tone, summary length, translation target language/style,
CV/minutes/report language and contrast/grayscale image outcomes. These describe
different outputs or source interpretation, not competing engine products. Independent
translation remains optional after OCR, never a mandatory extraction step.

AGENTS.md applies the same rule to future plugins: sell outcomes, not engines;
implementation is bounded inside confirmed price; declare duplicates with replaced_by.
Metadata is explicitly declared/reviewed, not inferred from translated names.
No promise of guaranteed “best”, handwriting support or perfect numeric recognition.

## Qualification

PASS LOCAL: 82 focused pure cases, lint/format/diff; exact-source mixed native OCR
and all four Arabic/English ruled/unruled automatic table fixtures passed. Local
full DB/container lifecycle NOT RUN. Hosted qualification still required.

Local lint/format, pure contract/security/fallback tests and synthetic native OCR/table
checks run separately from full hosted PostgreSQL/Redis lifecycle and document-worker
container qualification. Exact-head hosted results must be recorded in PR before merge.
Native workflow now additionally qualifies canonical mixed OCR without outbound AI and
automatic ruled/unruled Arabic/English tables with network disabled/non-root.

NOT RUN: Real-provider fallback on owner's two screenshots, VPS deployment, mobile
acceptance, representative extraction accuracy, paid checkout/load. The known Arabic
screenshot failed native OCR; removing the engine choice alone is not evidence that
real-provider fallback reads it correctly. Keep owner/provider acceptance separate.
