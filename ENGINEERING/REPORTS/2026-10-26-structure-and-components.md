# Architecture and reusable component review

Baseline main: 678904bb42635dc6cd0e90b3f499865286cb610d.
Owner authorizes new services, naming/organization and optional AI assistance.

## Architecture findings and changes

- FACT: services contains discoverable bounded plugins, schemas and prompts;
  builders owns deterministic file construction; providers owns external AI,
  native rendering, tables and owner-bound storage. Bot/API consume input schemas.
- DECISION: Retain those boundaries. No broad directory shuffle or extra framework
  is justified for adding these services. A new contact-card plugin demonstrates
  discovery, generic intake, worker execution and wallet delivery without core/bot
  branching. Keep existing service IDs, historical orders and administrator prices.
- IMPLEMENTED: interactive_card v1, default disabled, no AI or new dependency.
  Arabic/English portrait PDF, name/title and one to six explicit HTTPS buttons.
  No logo upload, hosted page, redirect service, ownership verification or QR in v1.
  No links are fetched. Unknown fields, active URL schemes and credentials reject.
  Customer labels/targets remain literal. Initial default price 3 SAR is configurable
  through existing admin pricing; no production enablement or price update occurs.
- VALIDATION: Unit checks cover exact PDF URI actions, six-link bounds, Arabic glyphs,
  input rejection and pure admission. Real DB tests cover one capture or full release
  after builder failure and no provider usage. Add business_card to isolated matrix
  and actual network-disabled non-root worker check. Exact-head hosted CI required.
- Remaining UI work: The seven-group taxonomy discussed with the owner is the target,
  not already applied wholesale. Existing document outcomes require a reviewed generic
  presentation grouping to avoid confusing duplicate menus without cancelling IDs.
  Add categories only when their implemented services are ready; no empty placeholders.
- Remaining service batches: barcode/QR generation and decoding, then menu/service
  lists, then labels/catalogs and commercial documents. Batch imports need bounded
  rows, duplicate/source references, preview and exact output manifests. Keep single
  and batch as input choices rather than separate implementations in core policy.

## GitHub research checked 2026-10-26

These are upstream candidates, not installed/benchmarked or adopted dependencies.
Repository license metadata was checked through GitHub; verify the exact release,
transitive dependencies and each model weight license before distribution.

| Upstream | Role | Repository license observed | Integration decision |
| --- | --- | --- | --- |
| https://github.com/heuer/segno | QR encoder, independent output formats | BSD-3-Clause | Candidate for static single/batch QR. Current ReportLab may already suffice; compare before adding dependencies. |
| https://github.com/zxing-cpp/zxing-cpp | Barcode/QR reading, Python bindings | Apache-2.0 | Candidate for bounded image decoding and independent read-back of generated codes. |
| https://github.com/PaddlePaddle/PaddleOCR | OCR and document parsing | Apache-2.0 | Benchmark Arabic/English receipts before replacing existing OCR; pin weights separately. |
| https://github.com/docling-project/docling | Structured document/table conversion | MIT | Evaluate difficult PDFs with the same source-fidelity gates; never silently replace strict native paths. |
| https://github.com/SYSTRAN/faster-whisper | Speech transcription, CPU int8 option | MIT | Candidate future audio-to-text/minutes input; not currently installed or measured. |
| https://github.com/QwenLM/Qwen3 | Open-weight text models | Metadata did not identify a license | README declares Apache-2.0 for its open weights; verify selected model card and repository code terms independently. |

Specific Arabic OCR model card:
https://huggingface.co/PaddlePaddle/arabic_PP-OCRv5_mobile_rec/blob/main/README.md
The publisher labels it Apache-2.0 and a text-line recognizer. It is NOT a complete
page detector/layout pipeline by itself. No Arabic-accuracy or performance claim
has been verified on this project's fixtures. Models downloadable from GitHub/HF
are not automatically zero-cost at runtime or appropriate for the current VPS.

## AI policy

Existing injected AI gateway already supports provider-required and conditional
paths, schema validation, bounded repair, quality review and conservative budgets.
The owner permits AI where it improves output. Use it for OCR review, semantic
organization, optional descriptions and source-bound content; keep exact prices,
calculations, barcodes, link targets and customer identifiers programmatic.

Evaluate models behind the provider boundary, using synthetic Arabic/English/mixed
fixtures first. Measure wall time, peak memory, resource contention and per-order
cost against existing provider/native baselines. Keep logical isolation and resource
limits on the shared VPS. Do not load heavyweight models into API/bot processes,
assume a GPU or available RAM, auto-download weights on startup, or enable a new
fallback on customer data without its authorization/quality gates.

Pass criteria: source fidelity and semantic correctness, exact numeric/contact
preservation, timeout/failure behavior, artifact cleanup, native editability,
mobile visual review and usage/cost observability. Benchmarks in upstream README
are upstream claims, not acceptance evidence for this deployment.
