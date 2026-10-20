# Master engineering roadmap

## PDF tools shared interactive-content boundary — 2026-10-21

- FACT: R02 from the comprehensive review reproduces on main 3af2a5a: empty AcroForm/Perms declarations and orphan Widgets (including indirect Subtype) pass page extraction. These operations cannot preserve form semantics or signatures.
- CHANGE: PDF tools v4 shares the existing conservative PDF-to-Word declaration/Widget checks, inspecting every source page before merge/extract/rotate. Malformed inspected annotations fail closed; ordinary links remain supported. PDF-to-Word retains its existing per-page inspection and extraction-limit ordering. Existing localized disclosures/errors and input-failure circuit classification apply.
- PASS LOCALLY: 155 focused builder/service/form/rotation/merge checks; three architecture gates, lint/format/diff and embedded worker Python syntax. Four before-fix fixtures reproduce acceptance. Added 12 PostgreSQL rejection cases and v3 prepared/unprepared upgrade coverage; 43 PDF-tools DB cases collected but NOT RUN locally (PostgreSQL unavailable). Hosted tests and worker qualification required before merge.
- SAFETY: Preserve administrator prices/activation and prepared v1–v3 results; incompatible unprepared work cancels/releases under existing guards. No AI, dependency, payment, migration, provider setting or server action. Synthetic fixtures do not validate signatures or prove native/mobile output quality.

## Bounded contextual numeric reuse in PowerPoint v7 — 2026-10-20

- FACT: Operator's targeted c69bf5f run reports zero added numeric/contact values and exactly two excess numeric occurrences in third-slide bullets on both attempts. Word/PDF passed the previous live run. Rejected response text/meaning is not retained, so the exact sentences and whether the repetition was useful remain unknown.
- POLICY CHANGE: PPTX v7 deliberately permits each exact numeric literal one additional use across the deck, on a different slide. Each slide keeps the original source occurrence budget; contacts keep the original whole-deck budget. New/changed values, in-slide excess and further repetition still fail. This accepts normal contextual recap patterns without deleting content. Prompts explain the limit; mandatory semantic review still checks meaning, coverage, duplicate records and padding.
- CHANGE: Production validation and isolated diagnostics share the same content-free violation iterator. The acceptance fixture now requires both original ID/amount literals in native output, including editable table cells. Version bump preserves administrator price/activation overrides, replays prepared historical files and cancels/releases unprepared old-version work under existing policy.
- PASS LOCALLY: 204 focused policy/reference/native/diagnostic/repair/acceptance checks, 17 existing native layout/quality checks and three architecture gates; global lint/format/diff clean. Added PostgreSQL cases exercise accepted context versus a simulated semantic rejection of reversed payment meaning through the normal review gateway, per-call settled cost, single capture/release and cached replay. Added v6 upgrade cases; 33 PPTX DB tests collected, NOT RUN locally (PostgreSQL unavailable). Full hosted qualification required before merge.
- LIMIT: This changes presentation policy, not source facts or exact-value matching. Token budgets do not prove semantic truth or source coverage. The supplied counts reproduce a failure class, not the unavailable exact historic response. No provider unpause, live call or production deployment here; build the new worker image and rerun isolated PPTX live acceptance before readiness claims. Word/PDF policies, call/cost caps and prices are unchanged.

## Content-free isolated PowerPoint rejection evidence — 2026-10-20

- FACT: Operator's live run on abe7bb8 passes Word smart and Text PDF smart; PPTX still fails pptx_source_tokens on both creation attempts. This does not identify an added/altered value versus excess repetition, or the affected slide field. No rejected response is retained in the historical report.
- CHANGE: In isolated acceptance only, resolve the same references and validate the original deck shape before counting excess numeric/contact occurrences against the synthetic case source. Record four fixed counts plus at most 32 locations with slide ordinal, fixed field/category and occurrence count. Print existing safe diagnostics for failed cases, avoiding a second report-extraction command.
- LIMIT: Locations identify occurrences beyond the source budget in traversal order, not which copy should be removed. Altered and wholly new literals both count as added. Numeric matches inside contacts mirror the existing source validator and may overlap contact counts. No values, hashes, source/model text, raw validation paths/context or candidate bodies are recorded.
- SAFETY: Same production schemas, prompts, prices/versions, fidelity rules, provider calls/correction caps, settlement and pause state. No fix or live readiness claim. Only already-mounted operational code changes; with the abe7bb8 worker image, a targeted isolated PPTX run needs no image rebuild.
- PASS LOCALLY: 92 focused observer/acceptance/repair/reference/diagnostic checks and three architecture gates; global lint/format/diff clean. Full hosted qualification required before merge; no local PostgreSQL/live-provider/server execution.

## Literal references for smart Word and PowerPoint — 2026-10-20

- FACT: Operator's live run on 62ab996 passes Text PDF smart after correction, but Word smart and PPTX still reject protected source tokens twice. Exact historical altered/extra/missing values remain unknown; this is not evidence of a renderer failure.
- CHANGE: Supply request-local references plus a literal dictionary for numeric/contact values in smart Word and PPTX source input. Restore known references before all schema, source-count, layout and semantic-review checks. Keep resolved continuations and native output free of generated internal references; raw valid responses remain compatible. PDF and Excel provider inputs remain unchanged.
- SAFETY: Reject unknown/incomplete current references, guesses and duplicate values through fixed reference errors and existing source guards. No fuzzy matching, inserted missing values, tolerance change, added calls, contract/version, price, activation or financial-policy change. Mapping stays transient in provider input, not JSON schemas or diagnostic logs; it is not encryption. Existing exposure reservations/caps apply to the larger input.
- PASS LOCALLY: 289 focused reference/source/service/repair/review/completion/acceptance checks; actual editable Word/PPTX readback verifies exact literals and no generated references. Three architecture gates and lint/format/diff checked. Ten PostgreSQL settlement/rejection/replay cases collected, NOT RUN locally; require full hosted qualification before merge.
- LIMIT: References reduce literal rewriting opportunities, not omissions, wrong associations or semantic errors. Existing semantic review remains required. No live call, provider unpause or production deployment here; isolated Word/PDF/PPTX live acceptance is still required before claiming readiness.

## Context-aware bounded schema repair — 2026-10-20

- FACT: Operator's new three-case live run reports document_source_tokens for Word/PDF and pptx_source_tokens for PPTX, on both creation attempts. These establish a protected-token fidelity rejection, not the precise historical changed/extra/missing occurrence. Source inspection confirms the correction previously discarded the rejected candidate and specific rejection category.
- CHANGE: Supply original source, a bounded rejected candidate and fixed content-free categories as untrusted input to the existing correction. Share the safe classifier with isolated diagnostics, forwarding trusted declarations through its schema observer. Preserve original contract/source for content review and reserve the complete actual repair request before sending.
- SAFETY: At most the existing two creation calls; unchanged schemas/versions, fidelity rules, prices/activation, caps, financial ledger and unknown-cost handling. Candidate is omitted entirely above 16384 characters, held transiently only and never logged. No production setting/unpause, deployment or live call here.
- PASS LOCALLY: 181 focused repair/review/completion/source/acceptance checks, three architecture gates and global lint/format/diff. Six DB-backed repair/rejection cases collected, NOT RUN locally (PostgreSQL unavailable); hosted execution must verify all three services with one capture/release, settled per-call usage, zero reserved credit and no duplicate delivery before merge.
- LIMIT: Simulated correction proves orchestration and guards, not that a live model will correct every result. Three-case isolated live requalification remains required; larger repair input may be rejected by existing budgets.

## Document plan guidance and safe rejection diagnosis — 2026-10-20

- FACT: Operator's 26/29 live sweep reports two generation constraints each for Word smart/PPTX, and a valid generation plus accepted review followed by needs_information for Text PDF smart. All supplied completions finish with stop and remain below the requested 8192-token cap. The generic constraint category cannot identify either historical failing rule; no truncation evidence appears in these calls.
- CHANGE: Explain existing document/deck/clarification requirements in provider-visible schema descriptions and clarify PDF handling of short supplied notes versus genuinely missing facts. Add fixed rejection codes for missing output/question, protected source tokens, document text and explicit slide-count mismatch; retain accepted/rejected payload boundaries. Isolated diagnostics record fixed plan booleans without source/output/question text.
- PASS LOCALLY: 251 focused schema/source/service/gateway/completion/acceptance checks, three architecture gates, global lint/format/diff. Rejection tests verify exactly two accounted creation calls and content-free codes; valid missing-information output remains observable and accepted by the same schema. Hosted qualification required before merge.
- SAFETY: Same customer inputs, versions, renderers, prices/activation, financial settlement, token caps and repair/call limits. Schema descriptions add prompt text within existing cost reservation. No provider unpause, live call or server deployment here.
- LIMIT: This corrects unclear guidance and insufficient diagnostics, not a proven root cause of the two historical constraints. New three-case isolated live acceptance is required before claiming those services fixed or enabling production AI.

## Integrated service presentation — 2026-10-20

- AUTHORITY: Owner requests integrated AI inside eligible services without an external AI option button. Existing required services already route automatically; mixed services retain explicit consent to change wording.
- CHANGE: AR/EN document buttons, mode explanation, previews and temporary-unavailability notice describe deliverables/content outcomes instead of engine selection. Help explains automatic internal processing. Retain format, language, heading and count controls; preserve existing values, old callbacks, service versions and request contracts.
- RUNTIME FACT: Latest operator inventory has all 16 services enabled, matching versions and all native capabilities present; production AI paused. Isolated live acceptance is operator-reported 26/29, with word_smart/provider_invalid, text_pdf_smart/needs_information and pptx/provider_invalid. Source presentation work is independent of diagnosing those failures from the pending results archive.
- PASS LOCALLY: 159 existing mode/output/AI-routing/readiness/portfolio/PPTX checks, three architecture gates, global lint/format/diff. Hosted lifecycle checks remain required before source merge. No new live-provider or production test was run in this presentation round.
- SAFETY: No provider unpause, budget/retry increase, price/payment/history change or production deployment. Integration is already internal; a label change does not fix provider validation or certify all-service quality.

## Document intake choice clarity — 2026-10-20

- FACT: Owner reports deployment of 248fafd; screenshots reproduce duplicate Preserve text choice/skip buttons and ambiguous provider-unavailable wording.
- CHANGE: Hide a skip alias already present in choice keys in the generic renderer; preserve explicit choices, distinct skips, old callbacks and schemas. Update AR/EN mode instructions and unavailable-service wording.
- PASS LOCALLY: 75 focused checks including 10 actual callback/in-memory-state regressions cover both languages, direct/smart/old-skip paths, optional titles, distinct skips and retained drafts after rejected submission; three architecture gates and global lint/format/diff. Full source-bound hosted checks required before merge.
- SAFETY: No service version, provider pause/credentials, pricing, wallet/order policy, dependency or migration change. Live provider output and updated Telegram/server verification remain separate.
- Evidence: [intake choice clarity](REPORTS/2026-10-20-intake-choice-clarity.md).

## Portfolio shared file-save recovery — 2026-10-20

- FACT: Main 88f98b1 includes #110. Fault injection reproduces failed writes/renames leaving temporary bytes that consume customer quota.
- CHANGE: Best-effort temporary-file/directory cleanup under the existing quota lock, preserving the original failure. Existing retention is the fallback when cleanup is unavailable. Refresh the 16-service source inventory to current versions/capabilities.
- PASS LOCALLY: 485 portfolio/source/output checks including six new failure/retry/cleanup cases; seven additional existing pure quota tests; architecture/lint/format/diff. Full hosted PostgreSQL/native worker checks required before merge.
- SAFETY: No plugin contract/version, AI allowance, prices/activation, financial/provider policy, dependency, migration or server change. Deployment remains one later batch.
- LIMITS: Catchable write/rename errors only; not a multi-artifact transaction or SIGKILL guarantee. Live provider/mobile/server acceptance remains separate.
- Evidence: [shared storage recovery](REPORTS/2026-10-20-shared-storage-recovery.md).

## PDF input rejection circuit classification — 2026-10-19

- FACT: Official main 25de614 includes #109, qualified by 2408 tests and 30 worker checks. Source inspection finds six explicit PDF content/limit/selection rejections still entering failed-service circuit samples.
- CHANGE: Exclude pdf_image_content, pdf_text_unreadable, pdf_text_too_long, pdf_tools_form, pdf_tools_limit and pdf_page_selection through the existing SQL input filter before its window limit. Generic file_invalid, unknown and provider/service failures remain counted.
- PASS LOCALLY: Three architecture gates, lint/format/diff and collection of 55 touched operational/PDF flow tests. PostgreSQL is unavailable locally. Hosted regressions cover repeated excluded inputs preserving queued work, three genuine/ambiguous failure cases behind newer input rejections, and actual form/page rejection under one-sample circuit/alert thresholds. Full hosted workflow/worker qualification required before merge.
- SAFETY: Same plugin versions, customer outputs, AI allowance, prices/activation, financial mechanics, provider pause and circuit thresholds/reset. No dependency, migration, production setting or server action. Existing disabled services are not re-enabled; deployment remains one later batch.
- LIMITS: Six explicit input codes only; no blanket file-error exemption, production incident claim or live-provider/mobile qualification. No audit rewrite.
- Evidence: [PDF input circuit](REPORTS/2026-10-19-pdf-input-circuit.md).

## PDF-to-Word interactive-content safeguard — 2026-10-19

- FACT: Official main ababfbd includes #108, qualified by 2385 tests and 29 native worker checks. A real filled PDF field has value Account 00999 absent from page text; v4 accepts conversion without it.
- CHANGE: PDF-to-Word v5 rejects catalog AcroForm/Perms declarations, including empty forms, and orphan page Widgets before provider calls/output. AR/EN intake and errors explain limits and request a static text-based copy. Ordinary links and text-only Form XObjects remain supported; malformed inspected annotations fail closed. Classify only this new rejection as customer input for circuit/alert exclusion; retain genuine-failure handling and test both paths.
- PASS LOCALLY: 68 focused new/existing PDF tests (53 existing pure cases without unavailable DB fixtures), three architecture gates, global lint/format/diff and workflow/worker syntax. Reproduced and closed an indirect Widget Subtype reference bypass during local adversarial review. Hosted flows add no-provider-cost rejection, release/no capture, notification/cleanup, and v4 upgrades/admin settings/cached replay. Offline non-root worker adds five declaration rejection fixtures. Full exact-head qualification required before merge.
- SAFETY: Same source-token/image/page/text guards, editable builder, AI allowance, dependencies, prices/activation and financial/provider policy. Prepared old files replay; unprepared old work cancels/releases through existing guards. No production action; deployment remains one later batch.
- LIMITS: Conservative rejection, not form flattening, field conversion or signature validation. Synthetic permission fixtures are not cryptographically signed files. Other annotations and original layout remain outside this qualification; live/provider/mobile acceptance NOT RUN.
- Evidence: [PDF Word form safeguard](REPORTS/2026-10-19-pdf-word-form-safety.md).

## Long OCR Word whitespace fidelity — 2026-10-19

- FACT: Official main 3e6ff34 includes PDF merge order (#107), qualified by 2354 tests and 28 native worker checks. Native DOCX readback reproduces loss of internal whitespace at the 12000-character chunk boundary while TXT remains intact.
- CHANGE: ImageToText v6 retains the delimiter in the preceding Word chunk and no longer strips the remaining text. Existing outer trim, artifact threshold, paragraph/source limits, editable builder and recognition/review routes remain unchanged.
- PASS LOCALLY: 48 focused export/source/follow-up/service tests (16 existing pure tests without the unavailable DB fixture), three architecture gates, global lint/format/diff and workflow/worker syntax. Hosted flows cover long exact text, cached v5 replay without rebuilding, single call/capture/cost, and v5 cancellation/admin settings. Offline non-root worker adds Arabic/English DOCX/TXT readback with injected recognition. Full exact-head hosted qualification required before merge.
- SAFETY: Same customer inputs, AI calls, dependencies, prices/activation, financial/provider policy and production settings. Prepared output replays; unprepared old work cancels/releases through existing guards. Deployment remains one later batch by owner request.
- LIMITS: Word paragraph structure, XML-safe text handling and outer trim remain; no original-layout or arbitrary control-character retention claim. Export checks do not certify OCR accuracy or native mobile appearance. Live acceptance NOT RUN.
- Evidence: [OCR long-text whitespace](REPORTS/2026-10-19-ocr-long-text-whitespace.md).

## Explicit PDF merge-file order — 2026-10-19

- FACT: Official main 55010c8 includes PPTX contact direction (#106), qualified by 2321 tests and 27 native worker checks before merge. PDF merges previously followed upload order only.
- CHANGE: PDF tools v3 adds optional file_order for merge only, after uploads. Arabic/Western/Persian digits and existing comma/space syntax express a complete permutation; skip/omitted/null keeps upload order. Entire source files move as units; internal page order is unchanged. AR/EN previews state actual file sequence. Reuse a bounded helper extracted from ImagesToPdf without changing its v3 contract.
- PASS LOCALLY: 154 focused merge/order/image/rotation/native-service tests, including all 2–5-file permutations and unchanged image-order tests; three architecture gates, global lint/format/diff and workflow/worker syntax. Hosted flows extend zero-AI capture, invalid admission, cached merge replay and v1/v2 upgrades/admin overrides. Native offline worker adds merged source-image readback. Full exact-head qualification required before merge.
- SAFETY: Same PDF builder, page/byte limits, forms/signature/encryption rejection, ownership, prices/activation and financial/provider policy. No new dependency, AI call or production action. Prepared old outputs replay; unprepared older work cancels/releases through existing guards. Deployment remains one later batch by owner request.
- LIMITS: Numbers refer to actual upload sequence, not filenames or inferred page numbering. Reordering does not restore outlines/metadata, repair PDFs or rewrite page content. Live Telegram/mobile acceptance NOT RUN.
- Evidence: [PDF merge file order](REPORTS/2026-10-19-pdf-merge-file-order.md).

## PowerPoint direction with Arabic contact prose — 2026-10-19

- FACT: Official main 07ecdb3 includes acceptance contracts (#105), qualified by 2299 tests and 26 native worker checks before merge. Reopened native PPTX for «تواصل: help@demo.invalid» had rtl=0 in both title and body because identifier letters dominated Arabic prose.
- CHANGE: PPTX v6 reuses the existing Word contact/date matcher solely for direction detection. Titles, bullets, table heading direction and individual cells follow remaining prose; actual text, source tokens, fonts, count/density contracts and centered covers remain unchanged. Pure contacts stay LTR; mixed prose still follows its dominant script.
- PASS LOCALLY: 112 focused contact/source-count/service/native-layout tests (95 normal focused plus 17 pure native tests without the unavailable DB fixture); three architecture gates, global lint/format/diff and workflow/worker syntax. Hosted flow adds source-owned contact output and extends v5 cancellation/cached replay/admin overrides. Native offline worker adds exact-email/RTL readback. Full exact-head hosted qualification required before merge.
- SAFETY: Same customer inputs, one artifact, AI schema/prompt/review/call limits, price/activation and dependencies. Prepared v4/v5 files replay; unprepared legacy work cancels/releases under existing guards. No server or production action; deployment remains deferred to one later batch.
- LIMITS: Reuses conservative contact/date recognition, not a language detector or arbitrary-identifier parser. Native XML/text assertions are not PowerPoint/mobile visual acceptance; unknown contact forms retain existing dominant-script behavior.
- Evidence: [PowerPoint contact direction](REPORTS/2026-10-19-pptx-contact-direction.md).

## Acceptance output contracts for recent improvements — 2026-10-18

- FACT: Official main 9fd8e67 includes explicit image ordering (#104), qualified by 2278 tests and 26 native worker checks before merge. Synthetic acceptance inspected minimum PDF pages/nonempty PPTX/general Excel cells, but did not enforce selected slide count, exact native page count, rotation flags or required sheets.
- CHANGE: Extend internal Case expectations and enforce exact PDF page counts, complete declared rotation tuples, exact PPTX slide counts and required workbook sheets when declared. Existing variable-layout minimum PDF policy remains. Current plan exercises reordered images, optional minutes titles and three-slide PPTX, requires CSV Columns, and adds one provider-free rotation case (29 cases/16 services; same AI case count/caps).
- PASS LOCALLY: 43 acceptance/contract tests; three architecture gates and global lint/format/diff. Hosted DB tests exercise three current native cases with zero provider calls/single capture each, plus output-contract failure producing REVIEW_REQUIRED with no capture or stranded reservation. Full exact-head hosted suite/non-root worker qualification required before merge.
- SAFETY: No live acceptance execution, provider call, production access, budget increase, plugin/schema/version/price/activation change or dependency. Existing production-isolation/fresh-database guards and one-batch deployment deferral retained.
- LIMITS: Structural expectations do not prove semantic completeness, actual image order, native/mobile appearance or all output filenames. Those remain covered by dedicated native tests and representative output review. Source qualification is not production acceptance.
- Evidence: [Acceptance output contracts](REPORTS/2026-10-18-acceptance-output-contracts.md).

## Explicit image-to-PDF page order — 2026-10-18

- FACT: Official main d0366a0 includes summary references (#103), qualified by 2225 tests and 25 native worker checks before merge. Image PDF pages previously followed upload order only.
- CHANGE: Images-to-PDF v3 offers optional page_order after uploads and before orientation. Western/Arabic decimal digits, commas/Arabic commas/spaces are accepted; each uploaded image must appear exactly once. Skip/omitted/null keeps upload order. Result preview names the exact source-image order in AR/EN.
- PASS LOCALLY: 74 order/native pixel/source-preservation/service tests, including all bounded permutations for 1–5 images, invalid admission, omitted/null defaults, EXIF-aware per-page orientation and literal pixels. Three architecture gates, global lint/format/diff and worker syntax. Hosted tests extend zero-provider cost/capture, invalid-order admission and v1/v2 upgrades/prepared replay. Full exact-head qualification required before merge.
- SAFETY: Existing native renderer, limits, ownership, metadata removal, price/activation, file count, zero-AI policy and ledger unchanged. No omission/repetition, crop, new dependency or production change. Existing version guards cancel/release unprepared legacy jobs and replay prepared results. Deployment remains one later batch by owner request.
- LIMITS: Image numbers refer to actual upload sequence, not filenames or inferred document pages. Reordering does not restore quality reduced by Telegram; send files for source resolution. Live Telegram visual acceptance NOT RUN.
- Evidence: [Image PDF order](REPORTS/2026-10-18-images-pdf-page-order.md).

## Inline source references for summaries — 2026-10-18

- FACT: Official main 41b0865 includes optional meeting-minute titles (#102), qualified by 2211 tests and 24 native worker checks before merge. Summary v2 showed citation mapping only inside the attached TXT report.
- CHANGE: Summary v3 numbers displayed points and adds a localized source-paragraph reference line to each. Chat and report use identical ascending source IDs, without mutating AI plans or source text. The notice explicitly distinguishes references from semantic/completeness certification.
- PASS LOCALLY: 45 summary/source-reference/service tests, including seven dense points with 80 references and Telegram chunk limits; three architecture gates, global lint/format/diff and workflow/worker syntax. Hosted coverage extends one-call/repair capture, cached v1/v2 replay and unprepared upgrade cancellation preserving administrator prices. Full exact-head hosted qualification required before merge.
- SAFETY: Same customer inputs, artifact count, AI schema/prompt/review, cost/repair limits, price/activation, financial policy and dependencies. Prepared historical results replay unchanged; no new provider stage or production action. Deployment deferred to one later batch by owner.
- LIMITS: Source IDs refer to nonempty physical input lines, not sentence-level evidence or proof of semantic accuracy. A long source paragraph remains one source unit; existing semantic review is unchanged.
- Evidence: [Summary inline references](REPORTS/2026-10-18-summary-inline-sources.md).

## Optional meeting-minute titles — 2026-10-18

- FACT: Official main 8b0b451 includes explicit PPTX counts (#101), qualified by 2183 tests and 23 native worker checks before merge. Meeting minutes still required a title before language/source intake.
- CHANGE: Minutes v4 makes the existing first title field optional through the generic Skip action. Missing/null titles use a neutral Arabic/English heading in the selected document language, shared by complete review and Word/PDF. Supplied titles retain existing validation; no name/date is inferred from source.
- PASS LOCALLY: 65 focused title/source/action/service tests; three architecture gates; global lint/format/diff and workflow/worker syntax. One existing LibreOffice export test excluded because the binary is unavailable locally; full hosted qualification remains required. Added hosted coverage includes dispatcher skip, native approved output, single call/capture, cached replay and v3 upgrades preserving administrator overrides.
- SAFETY: Same source classification, mandatory approval, artifact pair, provider limits, price/activation, dependencies and financial policy. Existing version guards cancel/release unprepared legacy work and replay prepared files. No server changes; deployment remains one later batch at owner request.
- LIMITS: Skip uses a visible generic heading, not a titleless document or automatic source-based title. Native structure/text checks do not replace live-provider/Telegram visual acceptance.
- Evidence: [Optional minutes titles](REPORTS/2026-10-18-minutes-optional-title.md).

## Explicit PowerPoint slide counts — 2026-10-18

- FACT: Official main 4eeecd8 includes CSV column summaries (#100), qualified by 2139 tests and 22 native worker checks before merge. PowerPoint count instructions in source prose were prompt-only, without a separate count contract.
- CHANGE: PPTX v5 asks an optional 1–30 slide count before content, accepting Western/Arabic decimal digits and including the cover. Request-local schema exposes exact minItems/maxItems and enforces the count during generation, revalidation and continuation. A trusted prompt names the selected output count separately from source facts; skip retains legacy automatic behavior.
- PASS LOCALLY: 86 focused count/source-contract/service/palette/native tests; three architecture gates, global lint/format/diff and workflow/worker Python syntax. Added hosted flows cover exact output, existing bounded repair and release/cost, invalid admission, approval reuse, cached retry and v1/v3/v4 upgrade/admin overrides. Native worker qualification adds 1/3/30-slide output checks. Full hosted qualification required before merge.
- SAFETY: Same renderer, source tokens, file result, administrator price/activation, provider/financial limits and dependencies. Prepared historical output replays; unprepared older jobs release/cancel through existing version guards. No extra AI call allowance, dependency, migration or production action. Owner defers deployment to one later batch.
- LIMITS: Exact count applies to the separate selected field; automatic/free-prose counts remain best effort. Count validation does not prove semantic completeness or fit every dense source; existing density/budget/source safeguards remain active.
- Evidence: [PowerPoint count contract](REPORTS/2026-10-18-pptx-slide-count.md).

## Source-owned CSV column summaries — 2026-10-18

- FACT: Official main 40aa7fa includes provider-free PDF rotation (#99), qualified by 2124 tests and 21 native worker checks before merge. CSV review had row-level audit but no compact per-column quality view.
- CHANGE: CSV v3 adds a native Columns sheet with source/Data headings and nonempty/empty/distinct-nonempty/trimmed counts for each original column. Uses exact case-sensitive post-rule values, includes duplicate records, excludes generated references, and explains static counts and literal emptiness in AR/EN. Customer headings remain exact literal text; counts are native integers, never formulas.
- PASS LOCALLY: 69 focused profile/CSV/similarity/whole-word-layout tests; three architecture gates, global lint/format/diff. Added/extended hosted flows cover zero-AI capture, cached retry and v1/v2 upgrades/admin overrides, including a historical workbook without Columns. Native worker qualification gains bilingual column-count checks. Full exact-head hosted workflow required before merge.
- SAFETY: Same inputs, price/activation, source rows/order/cell values, one artifact, similarity limits, provider/financial policy and dependencies. Existing version guards cancel/release unprepared legacy jobs and reuse prepared legacy files. No production action; owner requests one deployment after improvements.
- LIMITS: Counts describe literal values at creation, not business correctness, inferred missing data or spreadsheet formulas that recalculate. Native structure/readback is separate from mobile appearance acceptance.
- Evidence: [CSV column summaries](REPORTS/2026-10-18-csv-column-profile.md).

## Provider-free selected PDF page rotation — 2026-10-17

- FACT: Official main a4a307d includes translation contact fidelity (#98), qualified by 2081 tests and 20 native worker checks before merge. PDF utilities previously offered merge/extract only.
- CHANGE: PDF tools v2 adds selected-page rotation by an explicit additional clockwise 90/180/270 degrees. Keeps every source page in original order; modifies only selected rotation flags, normalizes modulo 360, retains text/content streams/images/page boxes. Conditional angle field and AR/EN prompts explain additive rotation versus extraction order.
- PASS LOCALLY: 55 native builder/contract/injected-service and existing merge/extract tests; three architecture gates; global lint/format/diff. New hosted flows cover no-AI cost/capture, invalid admission, failure/release/ownership, prepared retry and v1 upgrade/admin overrides. Non-root network-disabled worker qualification adds an image/page/order preservation check. Full hosted workflow required before merge.
- SAFETY: Existing limits, encrypted/form/signature rejection, price/activation, financial policy and dependencies retained. Prepared v1 files replay; unprepared v1 jobs cancel/release through existing guards. No new service, AI call, migration or production setting change. Owner confirms development first and one production deployment later; no server action.
- LIMITS: Rotation changes page display, not OCR, deskew, cropping, compression or original-layout reconstruction. Outlines/metadata remain unsupported as disclosed; signed/form PDFs stay rejected. Structural/native fixture evidence is not universal mobile-viewer acceptance.
- Evidence: [selected PDF rotation](REPORTS/2026-10-17-pdf-page-rotation.md).

## Translation email and URL fidelity — 2026-10-17

- FACT: Official main 94147fa includes editing reports (#96) and CI image fallback (#97), qualified by 2051 tests and 20 native worker checks before merge. A baseline reproduction accepts changed@example.invalid for source@example.invalid in independent text translation despite prompt instructions.
- CHANGE: Translation v2 checks exact email/HTTP(S)/www URL occurrence counts per original nonempty source line, using the existing contact-token matcher and request-local schema. Missing/changed/added/repeated/moved tokens trigger the existing bounded repair; no extra review call or retry allowance. Numeric/source/blank-line checks remain.
- PASS LOCALLY: 78 pure contract/service tests, three architecture gates, global lint/format/diff. Added hosted tests cover AR/EN success and one repair, persistent contact changes releasing credit, provider cost accounting, and v1 cached delivery/unprepared cancellation preserving administrator prices and activation. Full hosted workflow required before merge.
- SAFETY: Same customer inputs, files, prices and activation; historical prepared output replays unchanged. No core/ledger/provider budget/AI adapter/other translation path/dependency/migration/production change. Deployment remains deferred by owner.
- LIMITS: Conservative literal token recognition, not all contact formats or semantic correctness. Existing matcher includes adjacent punctuation in URLs; source spelling/case/punctuation must remain exact. No live-provider or Telegram qualification claimed.
- Evidence: [translation contact fidelity](REPORTS/2026-10-17-translation-contact-fidelity.md).

## CI official-image registry fallback — 2026-10-17

- FACT: Official main 409828c includes editing comparisons (#96), qualified by 2037 tests and 20 native worker checks before merge. Previous main a898e82's post-merge run 39032364723 failed twice before checkout while pulling ECR PostgreSQL: Data limit exceeded. No application test ran in those failed attempts.
- CHANGE: Pull the existing three official image tags after checkout, bounded to one 90-second client pull per ECR/Docker Hub candidate. Start only disposable CI PostgreSQL/Redis through a separate run/attempt-scoped Compose project, require existing health probes with --wait and no extra pulls, and always clean only that CI project. Selected Python reference feeds the unchanged native worker build.
- PASS LOCALLY: 17 helper/fallback/failure/context/architecture checks; lint/format/diff, workflow/Compose YAML and embedded Python syntax. Native worker qualification body is byte-for-byte unchanged. Hosted full workflow required before merge.
- SAFETY: Every original lint/format/migration/full-pytest/drift/production-Compose/native worker gate remains required; no continue-on-error, new credential or registry publisher. Production Dockerfile/Compose, dependencies, services, financial policy and settings unchanged. Deployment remains deferred by owner.
- LIMITS: Both registries may fail; CI then fails rather than bypasses gates. Tags are the existing series/version tags, not immutable cross-registry digest identity. Mocked fallback checks do not certify registry uptime or actual hosted service readiness.
- Evidence: [registry fallback](REPORTS/2026-10-17-ci-registry-fallback.md).

## Editing comparison reports — 2026-10-17

- OWNER: Continue service improvements/testing/merging without repeated approval; defer production deployment until development is complete. Official main a898e82 includes source-owned PDF table headings (#95).
- CHANGE: Text editing v2 keeps clean edited chat text and revision.txt, adding a deterministic changes.txt. It shows changed physical lines with exact before/after text and a full normalized-original appendix for context, including an explicit no-change result. Report labels follow source direction; no extra AI/schema/repair calls.
- PASS LOCALLY: 84 comparison/source-policy/existing-service/architecture checks; global lint/format/diff. Tests cover AR/EN, blank lines, CRLF, complete bounds, exact source/contact/zero preservation and partial-save cleanup. Full hosted lifecycle/cost/native worker qualification required before merge.
- SAFETY: Same inputs/price/activation, provider limits and financial policy. v1 upgrade cancels/releases unprepared work and replays historical one-file results without generating a report. New cached results replay both files. A failed second save attempts first-file deletion; existing TTL handles unreferenced files if deletion fails. No dependencies, migrations or production change.
- LIMITS: Literal line comparison is not a semantic/style/grammar assessment or a Microsoft Word tracked-changes file. Original context is present in the customer-owned report and follows existing retention. Live provider/Telegram quality NOT RUN; deployment remains deferred by owner.
- Evidence: [editing comparison report](REPORTS/2026-10-17-editing-change-report.md).

## Source-owned PDF table headers — 2026-10-17

- FACT: Official main 6d3a39f includes whole-word Excel sizing (#94). PDF-table direct export still uses generic columns and retains the source header as a data record; the portfolio review calls for an explicit source-first-row choice.
- CHANGE: PDF tables v4 adds a provider-free first-row heading choice for every extracted table. Data uses that row as native headers and starts at original R2; Source retains all cells and R1. Complete bilingual review shows every heading. Blank/duplicate/multiline/oversized or edge-whitespace headings are rejected rather than silently renamed. Existing optional visual Arabic recovery applies to Data headings only with explicit consent.
- PASS LOCALLY: 87 focused contract/native/source/Arabic/provider/architecture checks, global lint/format and diff checks. Native provider tests cover AR/EN ruled/unruled extraction; full DB lifecycle/upgrade and non-root worker source-heading export require hosted CI before merge.
- SAFETY: Existing direct/proposed modes retained; source mode never calls AI. Price/activation overrides and prepared-file replay retained; v2/v3 upgrade regression covers cancellation/release versus cached delivery. No dependency, migration, financial policy, provider pause, cap/retry or production change.
- LIMITS: The customer must decide whether every first row is really a header; merged/multiline/blank headers and per-table mixed choices are unsupported. Workbook readback is not native/mobile visual acceptance. Actual server deployment remains UNKNOWN pending operator output.
- Evidence: [source-owned table headers](REPORTS/2026-10-17-pdf-source-headers.md).

## Excel whole-word row sizing — 2026-10-17

- FACT: Official main f056e92 includes PowerPoint visual hierarchy (#93). Excel row sizing divided total text width by available width, underestimating paragraphs where whole words leave unused space at line ends.
- CHANGE: Shared Excel measurement now counts word boundaries, explicit blank lines and long unbroken values, with a request-local token measurement cache. CSV review, PDF-table workbooks and source-bound Office workbooks reuse this layout helper; cells, types, source references and native table ownership are unchanged.
- PASS LOCALLY: 41 focused wrapping/source tests; global lint/format/diff and three architecture gates. Arabic/English native workbook readback verifies six wide words receive at least six lines; exact values and the 409-point row-height ceiling survive. Full hosted CI/native worker qualification required before merge.
- LIMITS: This is a bounded sizing estimate, not Microsoft Excel/mobile visual certification. Very long cells still reach Excel's row-height ceiling; full text remains in the editable cell. No input/schema/service-version, provider-call, price/gate, dependency, migration or payment changes. Prepared files stay reusable. Owner now authorizes deployments after successful checks; no direct server connection is available here.
- Evidence: [Excel whole-word sizing](REPORTS/2026-10-17-excel-word-wrap.md).

## PowerPoint contrast and Arabic date display — 2026-10-17

- FACT: Official main aa58e16 includes selected document formats (#92). Native slide preview exposed reversed ISO-date components inside Arabic paragraphs despite intact source strings.
- CHANGE: PPTX v4 uses a dark cover/light text, restrained paper content background and explicit native table borders. Arabic paragraphs wrap ISO dates in display-only LTR marks; exact date characters retained, English unchanged. Existing measured geometry/font sizes/density rejection remain.
- PASS LOCALLY: Focused palette/native editability/service tests, lint/format/diff and architecture. Eight AR/EN fixture slides rendered in LibreOffice and inspected; Arabic cover/content rerendered after date fix and display order checked. Hosted full CI required before merge.
- LIMITS: No new AI schema/call, price/gate, retry/cap, dependency, migration or production change. Native shapes/text/tables remain editable. Preview is LibreOffice evidence, not Microsoft PowerPoint/mobile/provider semantic certification.
- Evidence: [PowerPoint visual hierarchy](REPORTS/2026-10-17-pptx-visual-hierarchy.md).

## Document delivery formats — 2026-10-17

- FACT: Official main 4098b7d qualifies explicit Office Word mode (#91). The existing Word/PDF bundle still always delivers two files while separate document entry prices remain DB-owned.
- CHANGE: Document v3 offers Word, PDF or both before one content intake; preserves direct/smart choices and optional title. Shared preparation stores only requested files and discloses selected output in both normal and visual review. Existing CV/minutes helper calls keep paired delivery unchanged.
- SAFETY: Same service price/admin activation, unchanged AI calls/bounds and rendering/source fidelity. Legacy internal inputs default to both; existing version guards handle old unprepared jobs. No retiring/rerouting other services or silently reconciling their prices, no financial/provider/migration/dependency changes or production action.
- PASS LOCALLY: 117 focused output/AI/source-policy/acceptance and existing bundle-service tests; lint/format/diff and architecture. New native/dispatcher/prepared-delivery/retry/upgrade flows require hosted full CI. Live provider/Telegram/production qualification NOT RUN.
- Evidence: [document delivery formats](REPORTS/2026-10-17-document-delivery-formats.md).

## Explicit Word intake before content — 2026-10-17

- FACT: Official main eeb33c1 includes qualified provider completion safeguards (#90); new live CV evidence is still unavailable. Office v7 exposed direct Word through a first-line directive rather than a visible choice.
- CHANGE: Office v8 asks file type, then required direct/smart choice for Word, then content. Excel skips the Word-only field and retains its AI contract. New direct requests preserve every supplied line; legacy internal parser/default behavior remains unchanged.
- SAFETY: Existing version/snapshot guards handle old drafts/jobs; upgrade regression covers v7 cancellation/release and administrator price/activation preservation. No core branching, renderer, service consolidation, price, provider, payment, dependency, migration, cap/retry or production setting change.
- PASS LOCALLY: Focused schema/routing/source fidelity/acceptance checks and existing Office service regressions, lint/format/diff. Dispatcher, lifecycle and upgrade flows require hosted full CI before merge; no new live-provider, visual redesign or production qualification.
- Evidence: [explicit Office Word mode](REPORTS/2026-10-17-explicit-office-word-mode.md).

## Explicit DeepSeek completion mode and truncation handling — 2026-10-17

- FACT: Official DeepSeek docs now state thinking/high effort defaults on; earlier adapter omitted a switch. Latest bilingual provider_usage remains unclassified without its archive. PR #89 is separate review-only work, preserved.
- CHANGE: Default explicit thinking.disabled for exact official Flash/Pro, validated operator override, fixed completion audit including finish reason and optional reasoning count (never text). Length-truncated JSON settles then uses the existing bounded repair; actual overrun accounting/pause retained.
- SAFETY: No new provider call, retry loop, cap/price/activation/service contract/migration/dependency change, historical rewrite, unknown-hold clearance or unpause. Other vendors/proxies/models untouched. Old billing is not a prerequisite for isolated development tests.
- PASS LOCALLY: 88 focused pure tests and lint/format/diff. New accounting flows and legacy DB-backed adapter checks require hosted full CI. New live provider/visual/production qualification NOT RUN; no permanent-reliability claim.
- Evidence: [provider completion contract](REPORTS/2026-10-17-provider-completion-contract.md).

## Complete portfolio review and accurate AI presentation — 2026-10-16

- FACT: Reverified official main ad1d2c1 and reviewed all 16 public contracts, catalog/admin/inventory, source policy tests and available acceptance evidence. Nine required AI, four conditional, three direct. CV v7 operator AR/EN PASS, bilingual provider_usage FAIL; new report/artifacts not supplied, no inferred root cause.
- CHANGE: Explicit optional-AI presentation metadata for four mixed plugins; shared required/conditional/none classification, registry validation, accurate no-AI admin text, paused mixed-option catalog notices and inventory warnings. Admission/activation/needs_ai, contracts, prices, versions, ledger, retries/caps and production pause unchanged.
- PLAN: Preserve six registry categories; diagnose current CV incident, then explicit document mode/unified Word/PDF entry, richer CV/PPTX/Excel and real image/PDF/text semantic acceptance. Preserve old contracts and reconcile differing admin prices before consolidation. No blanket activation or new unapproved services.
- PASS LOCALLY: focused policy/readiness/private/inventory tests; lint/format/diff. New DB flow coverage requires hosted full CI before merge; no new provider or production execution here.
- Evidence: [full review and phased plan](REPORTS/2026-10-16-service-portfolio-review.md).

## Resume visual hierarchy — 2026-10-16

- FACT: Operator CV v6 English acceptance passed: three calls, calculated SAR .070128, settled holds, no test active orders/reserved credit; production pause retained. Uploaded hashes matched, Word/PDF sample inspected. Review needed one JSON repair; this is one synthetic sample, not universal qualification.
- CHANGE: CV v7 opts into a smaller name/header hierarchy, muted contact text, restrained section accents, lighter long qualification leads, and plain skills/language blocks. Native editable text, existing language pages and source safeguards retained. Standard Word designs unchanged.
- PASS LOCALLY: 34 focused contract/layout checks including two dense Arabic/English native exports; 75 existing CV regressions; lint/format/diff. Nine three-language/theme fixtures plus the prior live short content rendered (13 pages); visual review found no clipping/overlap in these fixtures. Hosted full workflow required before merge.
- LIMITS: Typography improvement only; no new structured employer/date fields, provider calls, retry/cap/financial/price/gate/dependency/migration changes or production deployment. New v7 live quality NOT RUN.
- Evidence: [resume hierarchy](REPORTS/2026-10-16-cv-visual-hierarchy.md).

## Request-specific CV generation contract — 2026-10-16

- FACT: Targeted operator cv_en rerun failed twice in generation with generic constraint errors, before content review. Test orders/credit closed cleanly; production pause retained. The exact custom rule is not recoverable from that report.
- CHANGE: CV v6 exposes request-specific IDs, sections/counts, target language/count and summary presence/reference requirements in provider JSON schema. Existing fidelity checks remain; fixed custom codes make isolated diagnostics more useful without retaining content.
- SAFETY: No retry/cap increase, gateway/financial/renderer/dependency/migration/price/activation changes. One career intake and existing design preserved. A new worker image is needed for the service-code test; production containers need not be replaced for isolated acceptance.
- PASS LOCALLY: 69 focused contract/redaction/review/architecture checks and 56 existing CV input/fidelity/profile regressions; lint/format/diff/Bash syntax. Full hosted workflow required before merge. New live CV result NOT RUN; no claim of a proven English CV fix.
- Evidence: [CV generation contract](REPORTS/2026-10-16-cv-source-contract.md).

## Live output review and targeted acceptance diagnostics — 2026-10-16

- FACT: Uploaded #84 archive reviewed: all 40 artifact hashes match, 27/28 cases passed, 41 settled holds, calculated SAR .253417 versus cumulative call bounds 1.979355; production pause retained per operator.
- QUALITY: Native output inspection confirms small fixtures are readable. CV English standalone failed; exact validation stage unknown. CV/PPTX design remains basic; PDF-to-Word does not reconstruct the table grid. Long/dense Arabic and reverse translation need richer acceptance fixtures.
- CHANGE: Exact-case reruns, isolated-only content-free generation/review validation diagnostics, and separate calculated usage total. Original schema, bounded repair, budgets and production code/gates retained.
- PASS LOCALLY: 21 pure/architecture checks, lint/format/diff/Bash syntax. Hosted full qualification required. Targeted live rerun NOT RUN; no claim that CV failure is fixed.
- Evidence: [output review](REPORTS/2026-10-16-acceptance-output-review.md).

## Isolated all-service live acceptance — 2026-10-15

- OWNER AUTHORITY: Test all services now; historical cost reconciliation is not a prerequisite. Baseline c3a61f3 deployed/healthy/paused. Real synthetic C6F5D1AD succeeded: 458 input/93 output <=128, calculated SAR .000934, one settled hold; no universal/provider-quality/invoice claim.
- CHANGE: Default read-only plan and guarded isolated test execution for 28 cases across all 16 public services, normal job/budget/review/confirmation/replay paths, native artifact/readback checks and per-case safe reports.
- ISOLATION: Fresh uniquely named test DB, synthetic subject/test credit, dedicated files; no production pause/gate/ledger/price/history mutations. Conservative whole-run call-bound allowance SAR 5/96 calls plus DB limits. Failed/unknown usage retained; direct cases continue after AI block.
- PASS LOCALLY: 15 focused pure/architecture cases, lint/format/plan/Bash syntax. Hosted financial/native checks required before merge. Operator full live sweep and output review NOT RUN.
- Evidence: [isolated acceptance](REPORTS/2026-10-15-isolated-service-acceptance.md).

## Strict provider pause across admission paths — 2026-10-14

- OWNER AUTHORITY: Continue existing review and provider recovery preparation after #82. Source baseline 0576026; deployment of #81/#82 unconfirmed, last supplied operator runtime remains #80.
- FACT: UI pause hint was strict, but submit/Stars/provider reservation/readiness used generic truthiness; malformed falsey values could allow AI or raise an unclassified exception.
- CHANGE: One read-only pause reader reused by UI, order submission, Stars pre-checkout, budget reservation and readiness. Only absent row or explicit boolean false allows admission; malformed state blocks AI. Direct modes and legacy missing-setting default retained.
- PASS LOCALLY: 46 focused pure pause/UI/readiness/architecture tests and lint/format/diff. Hosted financial, concurrency, migration and native qualification required before merge.
- LIMITS: No live probe, pause bypass, financial reconciliation, rate/env/price/service/gate/dependency/migration changes. Unknown exposure stays held. Live cap verification remains blocked by operational pause and unresolved billing evidence.
- Evidence: [strict pause admission](REPORTS/2026-10-14-strict-provider-pause.md).

## Provider-paused customer intake — 2026-10-14

- OWNER AUTHORITY: Continue existing service review/improvement after #81 source merge. Baseline af8b118; #81 deployment not confirmed, latest operator runtime remains #80 (624c853).
- FACT: Required-AI selection/resume could collect a long draft before final submission rejected provider pause; translation followups checked AI-off but not global pause.
- CHANGE: Generic metadata-based required-AI early gate for new/resumed drafts, read-only pause hint in category browsing, and authoritative paused followup suppression. Existing drafts preserved; direct/mixed services remain browsable.
- PASS LOCALLY: 35 focused availability/catalog/order/architecture cases; lint/format/diff. Full hosted dispatcher/financial/native workflow required before merge.
- LIMITS: UI hint is not live-provider readiness. Mixed mode and pause races still checked by existing submit gate before reservation/invoice; no engine/ledger/rate/config/service-version/price/gate changes or unpause. Mid-collection pause does not discard inputs.
- Evidence: [paused intake UX](REPORTS/2026-10-14-provider-paused-intake.md).

## Provider usage audit and independent output cap — 2026-10-14

- OWNER AUTHORITY: Review supplied billing export and continue provider recovery improvements. Baseline/operator deployment 624c853 (#80), healthy with provider pause retained; backup EvFsFgt1.
- FACT: Two platform holds in the supplied hour; aggregate provider export has two requests. Calculated internal rates differ from exported hour rates/cache billing. Aggregate data does not identify exact per-attempt billed costs; unknown hold remains retained.
- CHANGE: Bounded cache/request/cap metadata in existing rate_snapshot JSON; calculations explicitly distinguished from invoices. Independent gateway cap breach pause after full usage settlement even within monetary bound. Historical records not rewritten.
- PREPARATION: Owner-only, read-only synthetic cap preflight (<=128 output tokens) prepares request/body hash/bound; no provider call, order, reservation, customer content or unpause.
- PASS LOCALLY: 60 focused audit/adapter/diagnostic/architecture tests; lint/format/diff. Hosted financial/lifecycle/native workflow required before merge.
- BLOCKED LIVE: Actual cap qualification still requires a separately controlled budgeted operational probe; preparation is not cap proof. No current pricing changes, invoice settlement, estimated unknown-cost reconciliation, secret changes or global resume.
- Evidence: [usage audit and cap guard](REPORTS/2026-10-14-provider-usage-audit.md).

## Smart Word and Text PDF source fidelity — 2026-10-14

- OWNER AUTHORITY: Continue improving all existing services with selective AI; baseline b2a41b6. #79 server deployment not confirmed; latest operator deployment remains #78.
- CHANGE: Office v7 smart Word and Text PDF v4 validate numeric/contact occurrence counters across all visible titles/sections/paragraphs/bullets/blocks/tables. Request-local schema applies existing bounded repair; injected responses and continuations revalidated before output writes.
- PASS LOCALLY: 103 focused source/service/template/architecture checks; global lint/format/diff. Full hosted lifecycle and native worker gates required before merge.
- LIMITS: Token checks do not prove semantics, names, correct field association or instruction/fact distinction. Direct literal modes, Excel provenance, prices/gates, dependencies/migrations and provider pause retained. No live provider or visual redesign claimed.
- Evidence: [smart document fidelity](REPORTS/2026-10-14-smart-document-fidelity.md).

## Source-bound Excel records and precision — 2026-10-14

- OWNER AUTHORITY: Continue office quality improvement after operator-confirmed #78 deployment, with provider pause retained. Baseline 63d2587.
- CHANGE: Office v6 Excel source IDs, verbatim cell quotes and conservative typed conversion checks; complete row/context accounting, revalidated continuations and original nonempty source lines in a separate worksheet. Word modes/intake retained.
- OUTPUT: Sortable native source references, quote-derived decimal precision, literal phone/formula-like strings and print padding. Source long lines split into exact reconstructable parts. No generated totals/formulas or extra AI calls during cached approval/delivery.
- PASS LOCALLY: 122 focused service/source/builder/policy/architecture checks and four final Arabic/English native Calc print pages; lint/format/diff. Full hosted lifecycle/native gates required before merge.
- LIMITS: Context/column/unit meaning and live provider/mobile quality remain unverified; no universal identifier, sorting, layout or output-capacity certification. Prices/gates, dependencies/migrations, financial policy and provider pause unchanged.
- Evidence: [Excel record source and precision](REPORTS/2026-10-14-excel-source-provenance.md).

## Optional Word/PDF content and design improvement — 2026-10-14

- OWNER AUTHORITY: Continue service quality work with selective AI. Baseline 9f22e97; operator confirms deployment, CV v5/PPTX v3 and retained provider pause.
- CHANGE: Word/PDF v2 optional direct/smart choice; omission/skip remains literal. Single source intake, ordered complete source IDs and per-ID numeric/contact fidelity; typed native design/section/block planning and existing bounded semantic review/repair.
- GENERIC FIX: Word prose direction excludes inline date/ASCII contact identifiers; trusted LTR runs/formatting marks keep embedded email/URLs readable without changing source characters.
- PASS LOCALLY: 89 focused service/policy/template/native/architecture cases and all six final rendered Arabic/English fixture pages; global lint/format/diff. Hosted lifecycle and native worker gates required before merge.
- SAFETY: Administrator prices/gates, dependencies/migrations, financial rules and provider pause unchanged. Live AI/mobile output quality, new deployment and historical invoice reconciliation remain unverified.
- Evidence: [optional Word/PDF improvement](REPORTS/2026-10-14-word-pdf-ai-improvement.md).

## Public service audit and source safety — 2026-10-14

- OWNER AUTHORITY: Review/improve all existing public services, permitting AI where useful. Baseline 995f03a, 16 customer services; private verification/retired OCR excluded.
- REVIEW: Nine required-AI, three conditional-AI and four direct contracts. Existing structured review/cost/cache controls retained; source review is not live output or deployment certification. Service-by-service gaps and ordered qualification documented.
- CHANGE: PowerPoint v3 source validation before admission, numeric/contact anti-invention counters, revalidated continuations and no-provider cached approval. Generic invalid-encoding/JSON digest returns safe input error before DB work; valid request hashes unchanged.
- PASS LOCALLY: 91 focused source/native-structure/policy/architecture cases; lint/format/diff. Full hosted financial/concurrency/native gates required before merge.
- SAFETY: No price/gate/dependency/migration/renderer/provider-pause changes. Last supplied server source remains 288d044; CV v5 deployment and real AI acceptance unconfirmed.
- NEXT: Source-bound optional Word/PDF improvement, then smart document/Excel/PPTX provenance and real OCR/text/minutes/image acceptance. No blanket AI toggles or silent unknown-cost clearing.
- Evidence: [public service quality review](REPORTS/2026-10-14-service-quality-audit.md).

## Single-entry AI CV content and design — 2026-10-14

- OWNER AUTHORITY: Improve the poor CV output, allow AI editing/translation/design, enter the career details once, and later improve other services selectively. Baseline 288d044.
- CHANGE: CV v5 removes duplicate English intake, edits/translates source-bound career segments, synthesizes an optional grounded summary, and uses the existing bounded semantic review/repair. Model selects source-owned typography, density, section order and native lead/bullet presentation. Complete Arabic body followed by English on a fresh page in one Word/PDF pair.
- GENERIC FOUNDATION: Opt-in typed Word design, mixed ordered blocks, section alignment and titled page breaks; standard document defaults retained. No service branches in bot/core/financial policy.
- PASS LOCALLY: 105 pure/source/builder/native regression checks and all eight rendered QA pages across three bilingual designs, a graduate and an academic fixture. Hosted PostgreSQL/financial/native workflow required before merge.
- LIMITS: Provider remains paused for the unresolved cost incident; no live AI calls, invoice reconciliation, deployment or customer/mobile acceptance claimed. Prices/default service gates, unrelated AI flags, dependencies and migrations unchanged.
- NEXT: After source qualification/deployment, reconcile the old uncertain exposure and qualify a real CV response. Later selective AI rounds use the shared needs_ai/review/cost/replay contracts, preserving direct tools where useful.
- Evidence: [single-entry AI CV](REPORTS/2026-10-14-cv-ai-single-entry.md).

## Required CV education intake — 2026-10-14

- OWNER AUTHORITY: Necessary fields must not show skip. Baseline e19f746; owner draft showed both education and experience absent in both languages, causing final validation failure.
- CHANGE: CV v4 requires education in root and English content/input fields, preserving optional experience. Localized prompts explain the requirement; existing generic skip guard reused, no bot/core branch.
- PASS LOCALLY: 66 pure/plugin/architecture cases, lint/format/diff. Hosted UI cases assert no skip and forged skip rejection without draft mutation; full CI required before merge.
- SAFETY: No price/activation/provider/template/financial/dependency/migration changes. New deployment and Telegram required-field acceptance NOT RUN.
- Evidence: [required CV education](REPORTS/2026-10-14-cv-required-education.md).

## Bilingual CV in one document — 2026-10-14

- OWNER AUTHORITY: Arabic-English in the same file after market-offer verification; implement and merge. Baseline 0d42d1d.
- CHANGE: CV v3 third language choice with conditional nested English intake; independently validated final bodies, paired Arabic/English sections in one editable Word/PDF pair. Four purpose profiles and existing compact layout retained.
- SAFETY: No automatic translation, invented counterparts, new dependency, bot/core branches, price/activation/provider changes. Bounded 9000 characters per language; no forced single-page promise.
- PASS LOCALLY: 59 focused pure/plugin/architecture cases and eight visually inspected pages across four native bilingual samples, lint/format/diff. Hosted native/zero-AI flow expanded; full CI required before merge.
- LIMITS: Server deployment, Telegram bilingual acceptance, translation and universal ATS qualification NOT RUN.
- Evidence: [bilingual CV](REPORTS/2026-10-14-bilingual-cv.md).

## CV purpose profiles and compact layout — 2026-10-14

- OWNER AUTHORITY: Integrate useful CV tools and research meaningful request choices. Baseline ad569b9.
- CHANGE: CV v2 optional professional/graduate/career-change/academic choices, headline and optional projects/languages/research/publications; source-preserving section ordering. Generic opt-in resume layout reuses existing docxtpl/native Word-PDF path; no imported third-party engine or copied assets.
- PASS LOCALLY: 45 focused pure/plugin/architecture checks and eight visually reviewed Arabic/English native sample renders, lint/format/diff. Full hosted financial/native regression gates required before merge.
- LIMITS: New runtime acceptance and ATS qualification NOT RUN. No factual rewriting, translation, date inference, provider/price/activation changes.
- Evidence: [CV profiles](REPORTS/2026-10-14-cv-profiles.md).


## Excel contact/text print layout — 2026-10-13

- OWNER AUTHORITY: Continue improving the extended PDF-table result. Baseline main d188667; supplied workbook retains all values but telephone/email wrap within a low row in LibreOffice print preview.
- CHANGE: Shared Excel layout measures installed DejaVu glyphs with explicit font sizes, separate bold/title metrics and bounded spacing estimates. Cache holds fonts only; missing-font fallback retained. No value/type/formula/table/reference/service-contract/payment/provider changes.
- PASS LOCALLY: 136 focused Excel/CSV/PDF-table/Arabic/architecture cases; global lint/format/diff. Rebuilt operator extraction has identical values in all five sheets; all LibreOffice print previews inspected and telephone/email fit on one line.
- LIMITS: Font substitution and existing column/row caps still limit general layout guarantees. Full exact-source hosted qualification required before merge; actual server re-export NOT RUN.
- Evidence: [Excel text layout](REPORTS/2026-10-13-excel-text-layout.md).

## Explicit Arabic visual-order PDF table recovery — 2026-10-13

- OWNER AUTHORITY: Continue fixing the operator-confirmed Arabic Excel display defect. Baseline main 4a852dc; actual supplied table output preserves numeric values but carries Arabic presentation forms in visual order.
- CHANGE: PDF tables v3 optional explicit visual-order recovery for simple Arabic cells in Data only; legacy/skip preserves extraction, Source stays exact, numeric/mixed/normal Arabic cells are untouched. Counts and confirmation disclose the selected transformation and limits.
- COMPATIBILITY: Existing confirmation/cache flow, prices and gates retained; stale unprepared v2 jobs cancel through existing release. No AI calls for correction, dependencies, migration, activation or provider-pause change.
- PASS LOCALLY: 57 focused pure/plugin/architecture cases, operator-extraction rebuild and global lint/format/diff; added hosted native/zero-AI/confirmation/upgrade/cache cases. Local Camelot subprocess unavailable; full exact-source CI required before merge.
- LIMITS: Explicit choice asserts direction, not content correctness; mixed cells intentionally remain unresolved. Server deployment/repeat Telegram acceptance NOT RUN.
- Evidence: [Arabic PDF table recovery](REPORTS/2026-10-13-pdf-tables-arabic-order.md).

## Read-only order diagnostics — 2026-10-13

- OWNER AUTHORITY: Continue development while the provider remains paused and historical cost exposure remains uncertain. Baseline d97c040; operator reports healthy deployment and max_tokens/8192, not a live provider trial.
- CHANGE: Private owner-authorized CLI, indexed prefix/full-UUID lookup with ambiguity rejection, bounded metadata-only repeatable-read/read-only PostgreSQL snapshot and five-second statement limits. Exact test-credit release evidence, recorded usage/overruns, unknown holds and provider pause/cap configuration; no raw content/customer identities.
- SAFETY: No provider call, row write, file mutation, financial settlement, automatic unpause or partial report on overflow. Unknown costs stay null. No migration/dependency/service contract/price/activation changes.
- PASS LOCALLY: 15 focused pure/architecture cases, lint/format/diff. Hosted financial/read-only/ambiguity/privacy cases added; full exact-source PostgreSQL/Redis/native qualification required before merge.
- LIMITS: Database metadata does not recover missing provider invoices or prove unknown-call billing. Deployment and historical reconciliation NOT RUN for this change.
- Evidence: [order diagnostics](REPORTS/2026-10-13-order-diagnostics.md).

## Provider output token contract — 2026-10-13

- OWNER EVIDENCE: f352c27 deployed; DeepSeek official endpoint/deepseek-flash with 8192 configured output limit. One settled call returned 15532 output tokens above held cost; another hold uncertain. Customer test credit released and provider paused. No automatic recovery authorized by diagnosis.
- FIX: Validated generic output-limit parameter; auto uses documented max_tokens for the exact official DeepSeek host and retains max_completion_tokens elsewhere. Same cap, bound, reasoning/model/timeouts and accounting; no named-service branching or financial-policy change.
- PASS LOCALLY: 29 adapter/config/architecture cases; hosted integration checks added for excess accounting/pause and retained uncertain exposure. Full exact-source PostgreSQL/Redis/native CI required before merge.
- LIMITS: Live API acceptance, deployment, billing reconciliation and operator unpause NOT RUN. Never clear unknown exposure or invent zero provider cost.
- Evidence: [provider contract report](REPORTS/2026-10-13-provider-token-contract.md).

## PDF to Word source token fidelity — 2026-10-13

- OWNER AUTHORITY: Accepted the review recommendation to improve current-service content fidelity. Baseline main 914df9d / PR #67.
- CHANGE: PDF-to-Word v4 request-local numeric/contact multiset validation across title/headings/body/bullets; preserve real source footers, exclude synthetic page markers, validate printable content and recheck injected plans before output writes. Existing bounded repair/content review reused.
- COMPATIBILITY: Same inputs/default gate; registry retains administrator prices/activation. Old unprepared v3 cancels via existing settlement; cached artifacts replay without regeneration. No migration/dependency/financial/provider/payment configuration changes.
- PASS LOCALLY: 46 focused source/plugin/Arabic-extraction/architecture cases, lint/format/diff. Full hosted PostgreSQL/Redis/native qualification required before merge.
- LIMITS: Token counts do not prove semantic associations, name/prose fidelity or original layout/table reconstruction. Deployment and representative live-provider acceptance NOT RUN for this change.
- Evidence: [source-fidelity report](REPORTS/2026-10-13-pdf-word-source-fidelity.md).

## All-current-service preflight and audited activation — 2026-10-13

- OWNER AUTHORITY: Develop and activate all services. Baseline main 3095ecf / PR #66; no direct server access available here.
- INVENTORY: 16 public outcomes plus private verification and retired OCR; only public canonical services enter the activation command.
- CHANGE: Validated plugin worker requirements, fixed environment-stripped native/import probes and read-only worker portfolio report. Explicit enablement reuses configured admin authorization and immutable per-service activation audit/fingerprint checks, retaining prices.
- SAFETY: All initial blockers prevent writes; later concurrent changes stop with reported partial progress. Existing enabled rows skip audit/reset. Unknown commit outcomes stay unknown. No new ledger/reservation, input/version/default flag, migration, dependency or provider/payment setting changes.
- PASS locally: Nine pure cases, three architecture gates, lint/format/diff and CLI help. Local worker probes correctly detect missing office/native OCR; Python engines/fonts present. Full suite collects 1357; exact-source hosted financial/native qualification required before merge.
- LIMITS/NEXT: Actual deployment/all-service activation and provider/mobile quality acceptance NOT RUN. Obtain host source/health/active-order evidence, then prepare verified update and worker activation. Future portfolio contracts remain separate; payment configuration stays last.
- Evidence: [portfolio activation report](REPORTS/2026-10-13-portfolio-activation.md), [runtime commands](../docs/SERVICE_ACTIVATION.md).

## Complete minutes review before approval — 2026-10-13

- OWNER AUTHORITY: Continue verified development and merges; runtime/manual/provider acceptance and payment remain later gates.
- BASELINE: Main 89d1508 / PR #65; no VPS deployment assumed.
- CHANGE: Optional generic bounded review details retain the 3000-character short preview. MeetingMinutes displays all categorized source units and complete owners/deadline conditions, not only two samples. Current UI language, UTF-16 message splitting and final-message-only approval apply to notification and order details.
- COMPATIBILITY: Same version 3, input/classification/continuation; cached legacy reviews and artifact replay preserved. No migration, dependency, new AI call, price/flag/activation or financial/provider-policy change.
- PASS locally: 39 review/schema/preview/DOCX cases, 19 existing pure service cases, three architecture gates and lint/format/diff. Full suite collects 1334; final hosted financial/native qualification required before merge.
- LIMITS: Long reviews span multiple messages; retry can repeat earlier messages. Real Telegram/mobile/provider acceptance and deployment NOT RUN. Correction uses cancellation/re-entry, without in-place edits.
- Evidence: [complete-review report](REPORTS/2026-10-13-complete-minutes-review.md).

## Meeting note name boundaries — 2026-10-13

- OWNER AUTHORITY: Continue the last development conversation; retain earlier verified-development/merge authority, manual acceptance and payment later.
- BASELINE: Main 5321530 / merged PR #64; VPS source not assumed updated.
- FIX: MeetingMinutes v3 retains common dotted AR/EN titles, uppercase initials, dotted Latin abbreviations and leading numeric list markers inside their original source unit. Explicit newline boundaries, numeric/date notation, duplicates and input limits retained. Uncertain mixed units remain review candidates.
- COMPATIBILITY: Unit IDs may change; existing version policy cancels unprepared v1/v2 work including unrendered continuation. Cached artifact delivery replays. Administrator prices/flags retained; no migration, dependency, core/provider/payment-policy changes or activation.
- PASS locally: 27 schema/preview/DOCX tests, 19 existing pure service cases and three architecture gates, lint/format/diff. Native/DB cases remain enabled in full hosted qualification, required before merge.
- LIMITS: Lexical protection is conservative, not complete language segmentation. Real provider/Telegram/mobile visual acceptance and deployment NOT RUN; later deployment must resolve unfinished minutes work.
- Evidence: [name-boundary report](REPORTS/2026-10-13-minutes-name-boundaries.md).

## Meeting action register and natural notes — 2026-10-12

- OWNER AUTHORITY: Continue development before manual trials; automated qualification required, payment last.
- BASELINE: Main f0bea18 / PR #63; latest operator VPS report is 1bf5e0d. No deployment assumed.
- CHANGE: MeetingMinutes v2 separates ordinary punctuation-delimited sentences, retains quoted units/classification, adds same-note quoted assignee/deadline and a localized action register in Word/PDF. Unknowns stay explicit; existing AI production review checks role/date meaning before customer approval.
- COMPATIBILITY: 80 notes/1200 characters each/12000 total. Prices/flags/payment controls retained; v1 unprepared jobs use existing version policy. Approved v2 continuation renders without another AI call. No dependencies, migration or activation.
- LIMITS: Abbreviations may split; ambiguous fragments go to review. Source spans/whole numeric tokens prove presence, not semantic assignment. Actual provider/manual visual acceptance deferred.
- Evidence: [minutes report](REPORTS/2026-10-12-meeting-action-register.md). Full exact-head hosted financial/native workflow required before merge.


## Administrator-only verification service — 2026-10-12

- OWNER AUTHORITY: Remove the verification-only customer category, retaining the tool for administrators.
- BASELINE: Main 1bf5e0d / PR #62; owner screenshots show updated category/admin labels, not complete runtime qualification.
- CHANGE: Generic validated admin_only metadata; echo is private. Customer menu/intake/followup/new-order and unpaid Stars pre-checkout recheck authenticated role. Admin management and verification menu remain available. Empty categories disappear dynamically; future public services can still use Other.
- HISTORY: Existing accepted jobs/results, idempotent replays and receipt/refund reconciliation retained; role change is not retroactive cancellation. No price/default/version/schema/migration/provider changes or payment activation.
- TESTING: Existing financial tests use echo as an explicit synthetic public plugin fixture, not production access policy; dedicated tests restore production private metadata and check role loss, stale buttons, no reservation, paid continuation and generic future-service restrictions. No assertions or financial cases removed.
- Evidence: [private verification report](REPORTS/2026-10-12-private-verification.md). Full exact-head hosted financial/native workflow required before merge; VPS/mobile private-menu acceptance separate.


## Consistent service labels and navigation — 2026-10-12

- OWNER AUTHORITY: Correct ambiguous names and simplify customer/admin browsing after editing/summary labels caused confusion.
- BASELINE: Main 9cb58fa / PR #61; latest source is not assumed deployed on VPS.
- CHANGE: Clear AR/EN outcome names, text/images/documents/PDF/data/professional category order and plugin-declared menu priority shared by customer/admin. PDF-to-Word belongs in PDF; intake/execution unchanged. Admin labels distinguish Manage services and Service prices; details show category and browser shows page count.
- COMPATIBILITY: Stable slugs, input contracts, versions, defaults, prices, Stars gates and financial operations. Registry metadata sync refreshes names without resetting administrator overrides. Future plugins inherit validated presentation priority and generic ordering.
- Evidence: [navigation report](REPORTS/2026-10-12-service-labels-navigation.md). Full exact-head hosted financial/native workflow required before merge; mobile/VPS acceptance separate.


## Grounded text summaries — 2026-10-12

- OWNER AUTHORITY: Improve the demonstrated near-copy and omitted meeting date; natural single-paragraph intake, automatic AI meaning review, preserved source evidence.
- BASELINE: Main d9f4ab2. Operator reported deployment/migration 0013 and enabled trials; source changes here are not deployed.
- CHANGE: text_summary v2 generates concise AR/EN points with known source citations, cited numeric/contact token bounds, duplicate/output/compression bounds and the existing production AI review/one-repair gateway. Full normalized source and references stay in the TXT report; customer message contains the summary only.
- COMPATIBILITY: No core branching, dependencies, financial policy, prices, flags, migration or payment activation. Old unprepared v1 jobs retain existing version-mismatch settlement; prepared results replay.
- LIMITS: Numeric/source checks cannot prove meaning. Fixture reviewer decisions exercise orchestration, not model accuracy; actual provider/customer acceptance remains required.
- Evidence: [summary report](REPORTS/2026-10-12-grounded-summary.md). Exact-head full hosted financial/native workflow required before merge.


## Confirmed administrator activation and durable cancellation — 2026-10-12

- OWNER AUTHORITY: Continue service activation controls with an explicit review of unfinished-order impact; preserve manual prices and professional quality boundaries.
- BASELINE: Main b810384 / PR #59. Source and runtime deployment remain distinct.
- CHANGE: Service details gain enable/disable proposals, five-minute actor-scoped fingerprint confirmation, impact counts and immutable history. Required version/AI/pause/Stars-price checks for enable; existing circuit reset retained.
- SAFETY: Gate/audit/fixed-target cancellation task commit together; separate worker recovery uses terminal-safe DB-only settlement/customer-first locks, no external refund claims. No earlier operation replay changes a later flag or cancels later orders. Bounded 100 orders/500 receipts; pending prior panel cancellation blocks enable.
- COMPATIBILITY: Additive 0013 migration and bounded worker cron, no plugin contracts/default flags/prices/provider/payment policy or dependencies changed. Existing commands/circuit behavior retained and not retroactively audited.
- Evidence: [activation report](REPORTS/2026-10-12-admin-activation-controls.md), [operator instructions](../docs/ADMIN_PANEL.md). Exact-head full hosted financial/migration/native workflow required before merge; VPS/mobile/provider/real Stars acceptance NOT RUN.

## Private service configuration inspection — 2026-10-11

- OWNER AUTHORITY: Continue professional service development and easier administrator controls, manual prices retained.
- BASELINE: Main 1c053b7 / PR #58; no VPS update or image-quality acceptance claimed.
- CHANGE: Read-only admin configuration browser, six entries/page, live refresh, stored/code version mismatch, activation/listing filters, local AI enabled/paused/cost-configuration evidence, current payment mode and Stars price; existing audited price shortcut.
- LIMITS: No provider request, native/worker probe, budget/admission approval or output-quality certification. Mixed services retain actual input-dependent admission; no guessed inputs. Retired plugins omitted; existing private-chat/owner gates retained.
- COMPATIBILITY: No contracts, migration, dependencies, pricing, activation, payment or financial policy changes. Customer draft/support state retained.
- Evidence: [configuration report](REPORTS/2026-10-11-admin-service-configuration.md), [admin instructions](../docs/ADMIN_PANEL.md). Exact-head hosted full workflow required before merge; VPS/mobile/provider acceptance NOT RUN.

## Image enhancement candidate selection and rejection — 2026-10-11

- OWNER AUTHORITY: Continue quality-first automatic AI improvement without engine choices.
- BASELINE: Main 5ecde14 / PR #57.
- CHANGE: Enhancement v3 evaluates source, native contrast and bounded sharpen evidence with the production AI gate. Deliver selected candidate only; no reliable improvement fails before artifact save and uses ordinary settlement.
- COMPATIBILITY: Administrator prices/flags retained; AI now required for this outcome, no extra intake option. Old unprepared v2 jobs settle under version policy; cached results replay. No new models/dependencies, activation or deployment.
- Evidence: [candidate review report](REPORTS/2026-10-11-enhancement-candidate-review.md). Full exact-head hosted financial/native checks required before merge; actual AI visual acceptance NOT RUN.


## OCR source detail and native candidate review — 2026-10-11

- OWNER AUTHORITY: Continue automatic AI quality work without customer engine choices; translation independent and optional.
- BASELINE: Main 462e8b2 / PR #56, no deployment claim.
- CHANGE: ImageToText v5 retains validated received bytes; metadata-free 2048px evidence, lossless native PNG; automatic production review of confident native text, one correction, maximum four accounted calls. Existing AI fallback gate retained.
- COMPATIBILITY: No new dependencies, activation, price, payment mode or migration; existing job/usage caps and prepared-result replay. Old unprepared contracts settle through version cancellation.
- Evidence: [OCR report](REPORTS/2026-10-11-ocr-source-review.md), [quality scope](../docs/AI_QUALITY.md). Exact-head hosted DB/financial/native workflow required before merge.
- NOT RUN: Real AI review, Arabic uploaded-photo acceptance, VPS/mobile/load. Blurred image restoration remains separate.


## Bot information and per-order Stars navigation — 2026-10-11

- OWNER AUTHORITY: Identify professional AI-supported services in bot information; make Stars payment accessible without a fictitious internal wallet.
- CURRENT SLICE: Arabic/English welcome/description, explicit authenticated `/syncprofile`, safe partial-failure/retry message, Stars-specific help and Payments label. Existing callback/old label compatibility, test-credit UI and private admin button retained.
- COMPATIBILITY: No activation, pricing, terms, ledger or provider-policy changes. Stars page does not query test-credit balance. Telegram metadata written only by the explicit admin command after deployment.
- Evidence: [bot information report](REPORTS/2026-10-11-bot-information.md), [usage](../docs/BOT_INFORMATION.md). Exact-head hosted workflow required before merge.
- NOT RUN: Production profile writes, VPS/mobile acceptance and actual Stars purchase/refund qualification.


## Private admin service prices — 2026-10-11

- OWNER AUTHORITY: Admin buttons and manual owner-set Stars selling prices, independent of provider expense; continuous verified development/merges.
- CURRENT SLICE: Private `/admin` and owner home button, six services/page with prices/state, order totals, Stars report, last-five immutable price edits. Reply-bound five-minute price proposal, frozen confirmation, server authorization, optimistic stale-price detection and atomic audit/idempotency.
- COMPATIBILITY: Additive migration 0012; no price defaults/activation/payment conversion. Paid prices retained, old unpaid invoices invalidated by existing policy. Customer draft/support FSM states preserved. Existing `/setstars` enters audited price change; `/setprice` test credit unchanged.
- Evidence: [admin report](REPORTS/2026-10-11-admin-service-prices.md), [usage](../docs/ADMIN_PANEL.md). Full hosted migration/financial/native verification required before merge.
- NOT RUN: VPS deployment and real Telegram/mobile ForceReply acceptance. Enable/disable confirmation, support buttons and rendered-image restoration remain later slices.



## Bounded automatic AI content quality — 2026-10-11

- OWNER AUTHORITY: Continue verified development and merges, internal automatic AI improvements, manual owner prices, independent optional translation.
- VERIFIED BASELINE: Main 2ac05a7 / PR #53; original-image PDF intake and bounded native worker retained.
- CURRENT SLICE: Production AI extraction reviews source/task/schema/candidate automatically; one creation repair shared by schema/content defects, final source-based review; at most five calls per extraction, ordinary job/global/user caps and usage ledger.
- COMPATIBILITY: No dependency/migration/service contract or activation changes. Prices, Stars policy, native paths and cached result replay preserved. Same-model review is not accuracy certification or rendered-file inspection.
- Evidence: [quality report](REPORTS/2026-10-11-bounded-ai-quality.md), [scope](../docs/AI_QUALITY.md). Exact-head hosted lifecycle/native gates required before merge.
- NOT RUN: Real-provider meaning/false-verdict acceptance, VPS/mobile/load and all-page visual AI review.


## Preserve received image quality in PDF — 2026-10-11

- OWNER AUTHORITY: Continue quality-first development after the full review; internal engines, manual prices, independent operating costs.
- BASELINE: Verified local/remote main f288f7a / PR #52. Separate pending AI-review/profile work preserved.
- CHANGE: ImagesToPdf v2 exact validated received-source admission; injected resource-bounded native PDF generation, shared per-worker capacity. Retain pixel/EXIF/output/storage limits and builder page behavior.
- COMPATIBILITY: Real contract bump preserves administrator enabled/SAR/Stars overrides; unprepared v1 cancels through existing settlement policy; prepared result delivery reuses the saved PDF.
- QUALIFICATION: Actual intake-to-PDF high-resolution pixel tests; full hosted lifecycle and additional native worker source gate required before authorized merge.
- Evidence: [Source-quality report](REPORTS/2026-10-11-images-pdf-source-quality.md). No pricing, activation, migration, model or payment changes; real Telegram/VPS quality/load NOT RUN.

## Automatic document image enhancement v2 — 2026-10-11

- OWNER AUTHORITY: Improve the weak document image result; one customer outcome, internal implementation selection, payment last.
- BASELINE: Main 47aee09 / PR #51; operator reported healthy deployment. Uploaded comparison is not the raw source and is not a fidelity fixture.
- CHANGE: One image question; opt-in exact validated received source; lossless decode and 2048px bound; conservative illumination/noise/luminance contrast processing; enhanced/comparison/source delivery order.
- COMPATIBILITY: Generic preserve_image default is a no-op for all existing plugins. v2 real contract bump preserves admin price/enabled settings; incompatible queued v1 releases, prepared results replay. No dependencies, migration, AI or payment changes.
- Evidence: [Enhancement v2 report](REPORTS/2026-10-11-document-image-v2.md). Full exact-head hosted lifecycle and twelve actual native worker gates required before merge.
- NOT RUN: Updated VPS/mobile acceptance, source-photo moire/faint handwriting/general OCR acceptance and production load.

## Completion navigation across services — 2026-10-11

- OWNER AUTHORITY: Home/another-service controls after any service; continue service development/activation, payment last.
- BASELINE: Main fbffa58 / PR #50; 1072 hosted cases and eleven native worker gates passed.
- CHANGE: Generic Telegram delivery sends one completion panel after all text/artifacts. Existing eligible plugin followups remain optional; ordinary services receive only Home/another-service. Existing drafts, purchase confirmation and cached retry policy retained.
- AUDIT: 18 registered plugins, one historical replacement, 17 customer-visible source entries including the test echo. Runtime enabled flags are UNKNOWN here; preserve DB-owned settings. Local file services first, provider-assisted semantics and proposed extensions need separate acceptance.
- Evidence: [Completion report](REPORTS/2026-10-11-service-completion-navigation.md), [activation plan](../docs/SERVICE_ACTIVATION.md). Full exact-head hosted/native qualification required before merge.
- NOT RUN: VPS activation/update, representative customer/mobile and real-provider acceptance. No default activation, migration, dependency, price, contract/version or payment change.

## Clearly optional result translation — 2026-10-11

- OWNER AUTHORITY: Add Home/another-service exits and explicitly optional translation after original OCR delivery.
- BASELINE: Main 7cf4b7c / PR #49; 1070 hosted cases and eleven native worker gates passed.
- CHANGE: Existing eligible followup panel now offers three separate rows: Home, another service, optional translation. Reuse ordinary navigation and owner-bound translation callbacks; no automatic draft/order/reservation.
- COMPATIBILITY: No contract/version, activation, dependency, schema, payment, price or engine change. Existing availability gates and original result retained.
- Evidence: [Optional translation navigation report](REPORTS/2026-10-11-optional-translation-navigation.md). Exact-head hosted regression/native qualification required before merge.
- NOT RUN: Updated VPS/mobile acceptance.

## Explicit original-text OCR guidance — 2026-10-11

- BASELINE: Main 444f25a / PR #48; 1070 hosted cases and eleven native worker gates passed.
- OPERATOR EVIDENCE: VPS HEAD 444f25a, healthy API/bot/worker and database/cache, successful migration. Pasted English wording differs from earlier English image, but source/service/translation step remains UNKNOWN.
- CHANGE: Explicit verbatim/no-translation/no-editing/source-instructions-as-data guidance in OCR prompt/output field description. Existing contract/version, routing/thresholds, cached results, costs/prices and optional independent translation unchanged.
- LIMIT: Model guidance is not deterministic fidelity validation. Require full exact-head hosted regression/native checks and separate live-provider/source acceptance.
- Evidence: [Verbatim OCR report](REPORTS/2026-10-11-ocr-verbatim-guidance.md). No new dependency, migration, activation or payment work.
- NOT RUN: Updated VPS/live-provider acceptance. Do not claim the ambiguous pasted output proves a specific engine bug.

## Unified customer outcomes, internal engines — 2026-10-11

- OWNER AUTHORITY: One OCR service, no customer local/AI selection; apply outcome-first policy to all current/future services. Payment work last.
- BASELINE: Main 7a7c5c2 / PR #47, 1043 hosted cases and ten native gates passed.
- SLICE: OCR v4 mixed native-first/classified AI fallback within one order/price; generic replacement metadata hides/rejects new legacy purchases and resolves old buttons to current-price canonical drafts. Retain historical execution/admin overrides.
- CURRENT AUDIT: All 18 plugins reviewed. PDF tables v2 automatically selects bounded extraction methods; document/heading choices describe outputs, not engines. Preserve format/language/operation and rewriting consent choices.
- SAFETY: Owner-bound bytes, numeric native thresholds retained, AI budgets unchanged, no extra fee/auto activation/migration/dependency/payment change. Confidence is not a correctness guarantee.
- Evidence: [Unified service report](REPORTS/2026-10-11-unified-service-experience.md). Exact-head full lifecycle and eleven native worker gates required before authorized merge.
- NOT RUN: VPS/mobile acceptance and real-provider OCR fallback on the owner screenshots.

## Original OCR and optional independent translation — 2026-10-11

- OWNER AUTHORITY: Extract original text first; translation remains independent with an optional result button. Continue verified development/merges; payment work remains last.
- VERIFIED BASELINE: Main 79d063e / PR #46; 1005 hosted tests and ten native worker gates passed.
- CURRENT SLICE: AI OCR v3 accepts images only. Both OCR plugins declare generic text followups to the existing translation service. Prefill the retained original result, then collect target language/style and use ordinary purchase confirmation.
- SAFETY: Owner/status/version/expiry checks, current target gates/schema/price, original text preserved, no truncation, no order/reservation on click, no active-draft replacement. Target printable-text/12000-character/80-line limits checked before offering the shortcut.
- COMPATIBILITY: No migration/dependency/payment policy or admin activation change. DB-owned price/enabled flags retained; queued old AI OCR contracts follow existing cancellation/release policy. Source content uses existing retention and draft TTL.
- Evidence: [OCR followup report](REPORTS/2026-10-11-ocr-translation-followup.md). Exact-head full lifecycle/native qualification required before authorized merge.
- NOT RUN: VPS update, real Telegram/provider/translation meaning and mobile acceptance for this change.

## Service categories and bounded browsing — 2026-10-11

- OWNER AUTHORITY: Finish/organize services; payment work last. Reuse existing payment policy without adding activation or pricing changes.
- VERIFIED BASELINE: Main 9633359 / PR #45; 977 tests and ten actual worker gates passed.
- CURRENT SLICE: Plugin-owned category metadata, six customer sections plus generic fallback; only currently enabled/payment-eligible services, no empty sections. Up to six services/page, back/previous/next, stale page clamp and safe empty-category response.
- COMPATIBILITY: No DB migration, dependencies, input contracts/version bumps, service activation or price changes. Legacy service callbacks still select directly; browsing preserves drafts and reserves nothing. No named service list in bot/core.
- Evidence: [category report](REPORTS/2026-10-11-service-categories.md). Exact-head full lifecycle/native CI required before authorized merge.
- NOT RUN: Server update/mobile acceptance and paid launch. Payment completion deferred per owner instruction.

## Optional lexical CSV candidate review — 2026-10-11

- OWNER AUTHORITY: Continue useful GitHub integrations and verified merges; no server/activation evidence inferred from continuation.
- VERIFIED BASELINE: Main 0b5603e / PR #44; qualified source passed 950 hosted tests and nine actual non-root/network-disabled worker gates.
- CURRENT SLICE: CSV v2 optional local RapidFuzz 3.14.6 report. Up to 200 records when enabled (usual review still 500); minimum differing-cell ratio >=90, no extra preprocessing, changed numeric/empty cells excluded. No AI, deletion, merging or same-entity probability claim.
- REPORT: Source-bound pairs/different column numbers; first 1000 pairs in stable source order, total and omissions disclosed. Data/Source and exact-equality Review preserved; static Similarities sheet.
- PASS LOCAL: 52 CSV/unit cases plus three pure architecture cases; lint/format/diff and single-package dependency delta, 977 suite cases collected. Local DB/native container qualification NOT RUN.
- COMPATIBILITY: Missing/null option keeps usual output. Registry version bumps to 2 and preserves DB-owned prices/enabled flags; queued v1 orders follow existing cancellation/release policy, not transparent cross-version execution.
- LOCAL/HOSTED evidence: [CSV similarity report](REPORTS/2026-10-11-csv-similarity.md). Full exact-head hosted lifecycle/native qualification required before authorized merge.
- NOT RUN: Server update, mobile workbook acceptance, representative false-positive/missed-pair usefulness and load; do not enable or market by passing synthetic checks alone.

## Document image contrast enhancement — 2026-10-11

- OWNER AUTHORITY: Continue recommended preview/image-quality improvements and verified merges.
- BASELINE: Main 38fbd5b and PR #43 visual-review foundation candidate 1f942a2; exact candidate/full hosted evidence required before each merge.
- CURRENT SLICE: Independent default-disabled image contrast/grayscale service; exact received bytes, processed PNG and left/right comparison; no AI or core branching. Existing packages promoted to explicit direct declarations with unchanged package/version sets.
- PASS LOCAL: 57 focused checks, real numeric OCR fixture after both modes, synthetic visual inspection, lint/format/diff; hosted lifecycle/native qualification required.
- Evidence: [document image report](REPORTS/2026-10-11-document-image-enhancement.md).
- NOT RUN: Server installation/enablement, representative customer image/mobile/load acceptance and commercial Stars pricing.

## Source-owned document visual review — 2026-10-11

- OWNER AUTHORITY: Continue recommended previews/image-quality improvements and verified merges.
- VERIFIED BASELINE: Main 38fbd5b / PR #42; 912 tests and seven native worker gates passed.
- CURRENT SLICE: Optional first-page PDF visual review for source-owned Word/PDF pairs; cached file delivery after approval, owner-bound preview retention and phase-safe notification/controls. No new dependency or migration.
- PASS LOCAL: 56 focused checks, native PDF first-page image and visual inspection, lint/format/diff; PostgreSQL/full native Word qualification requires hosted CI. Local LibreOffice unavailable.
- Evidence: [visual review report](REPORTS/2026-10-11-document-visual-review.md).
- NOT RUN: Server installation/enablement, customer/mobile/throughput acceptance; independent image enhancement is next.

## Service menu and confirmation price layout — 2026-10-10

- OWNER AUTHORITY: Prices only in the confirmation review, clearer service buttons and related workbook instructions.
- VERIFIED BASELINE: Main aef8b6a / PR #41; 904 tests and seven native gates passed.
- CURRENT SLICE: Name-only service buttons, price disclosure notice and separate price line in SAR/Stars confirmation; one workbook sheet per instruction bullet.
- PASS LOCAL: 27 UI unit checks, lint/format/diff, 912 tests collected. Full hosted dispatcher/payment/native qualification required before merge.
- Evidence: [price layout report](REPORTS/2026-10-10-service-price-layout.md).
- NOT RUN: Server installation and mobile visual acceptance.

## Telegram mobile UI review — 2026-10-10

- OWNER AUTHORITY: Fix screenshot issues and check related interface paths; continuous verified merge authority persists.
- VERIFIED BASELINE: Main 1421359 / PR #40; post-merge workflow 38075628816 SUCCESS.
- CURRENT SLICE: Adaptive full-width choice labels, separate cancellation/approval rows, display-only short references, complete UTF-16 preview splitting and localized service reviews independent of file heading language.
- Source UUIDs/ownership/financial policy remain authoritative; legacy previews retain fallback. Full IDs remain in order details for support.
- PASS LOCAL: 63 independent UI/provider/PDF-table/architecture checks; 904 tests collected; extended preview regressions and native-local prerequisite limits recorded in the report. Exact published head requires full hosted lifecycle and seven native gates before merge.
- Evidence: [mobile UI report](REPORTS/2026-10-10-mobile-ui.md).
- NOT RUN: Updated device/font screenshots, live AI heading qualification, server update.

## PDF tables to Excel — 2026-10-10

- OWNER AUTHORITY: Complete independent development slice; prior verified continuous merge authority persists.
- VERIFIED BASELINE: Main 822efbd / PR #39; 829 tests and six native worker gates passed on its published head.
- CURRENT SLICE: Default-disabled `pdf_tables_excel`, Camelot 2.0.0, bounded text-only PDF extraction with lattice/stream; source-preserving Excel and mandatory structure confirmation.
- Optional AI proposes headings only; original cells remain literal text in Data/Source sheets with stable references and Review metrics. Metrics do not prove extraction correctness.
- PASS LOCAL: 44 independent plugin/native/architecture checks; full hosted lifecycle/native qualification required before merge.
- Evidence and constraints: [PDF tables report](REPORTS/2026-10-10-pdf-tables-excel.md).
- NOT RUN: Representative customer PDF/mobile Excel/live AI/Telegram, server installation, activation and commercial prices.

## Extractive source-bound key points — 2026-10-10

- OWNER AUTHORITY: Continue independent useful services under prior verified merge
  instruction. Current bounded slice implements extractive points, not free-text claims.
- VERIFIED BASELINE: Main e624000 / PR #38. Post-merge workflow 38070202160,
  job 114265871891: 785 tests, migration/drift, Compose and all six native worker gates PASS.
- CURRENT SLICE: Default-disabled `text_summary`: 12000 characters, 2–80 nonempty
  source lines (one paragraph per line); short/standard selects at most 3/7 points,
  always fewer paragraphs than the source. Original source strings only in source order.
- AI returns strict unique known integer IDs only; no AI-produced prose is delivered.
  Heading language AR/EN does not translate source. Chat points plus owned UTF-8
  summary-source.txt containing selected points and all numbered source paragraphs.
- Semantic importance, coherence and omitted context remain unqualified; exact quotes
  do not establish summary completeness or customer value. Live provider/user acceptance
  required before activation; rewriting/study questions remain separate proposals.
- PASS LOCAL: 90 independent source/service/architecture checks, lint/format/diff;
  829 tests collected, including 30 new unit cases and 14 new DB lifecycle cases.
- LOCAL/HOSTED evidence: [key-points report](REPORTS/2026-10-10-text-summary.md).
  Exact published head must pass full lifecycle/native CI before authorized merge.
- NOT RUN: Live provider/Telegram, server update, pricing and activation.

## Independent proofreading and rewriting — 2026-10-10

- OWNER AUTHORITY: Continue the proposed independent writing/proofreading service;
  prior continuous verified merge instruction persists. No deployment/activation implied.
- VERIFIED BASELINE: Main 68ae143 / PR #37. Post-merge workflow 38069092755,
  job 114262659938: 740 tests, migration/drift, Compose, all six actual native worker gates PASS.
- CURRENT SLICE: Default-disabled `text_editing`: original-language Arabic/English
  pasted text, proofread-only or rewrite; tone intake shown only for rewrite.
  12000 characters/80 nonempty source lines; output bounded to 24000 characters.
- Exact source ID coverage/order, per-line numeric/contact-token occurrence counts,
  original blank lines and owned UTF-8 revision.txt. Existing AI budget/one repair,
  cached delivery and financial policy reused; no new vendor SDK/dependency/migration.
- Structural validation cannot prove language, meaning, names, negations, qualifiers
  or promises. Draft needs customer review and real-provider semantic qualification.
- PASS LOCAL: 82 service/source/architecture checks and lint/format; 785 tests collected.
- LOCAL/HOSTED evidence: [editing report](REPORTS/2026-10-10-text-editing.md).
  Exact published head must pass hosted lifecycle/native gates before authorized merge.
- NOT RUN: Live AI/Telegram, server update, operator pricing and activation.
  Next bounded proposals: source-bound summaries/revision and actual-fact CV writing.

## Independent source-bound text translation — 2026-10-10

- OWNER REQUEST: Add separately discoverable text translation and useful paid services;
  preserve modular architecture and existing source/payment/quality boundaries.
- VERIFIED BASELINE: Main 99f4b6f / PR #36; post-merge workflow 38066931365 passed
  708 tests and every existing financial/native document qualification gate.
- CURRENT SLICE: Default-disabled `text_translation`: pasted text, AR/EN target, four
  existing styles; 12000 input characters/80 nonempty lines, 24000 output characters.
- Strict source IDs exactly once, numeric-token multiset per line, original ordering
  and blank lines retained; text and UTF-8 TXT delivery. Shared existing numeric validator
  moved without changing the OCR contract; old imports retained for compatibility.
- PASS LOCAL: 49 independent service/schema/OCR-number/architecture checks; lint/format.
  Full lifecycle/financial/DB/native hosted gates required before authorized merge.
- NOT RUN: Live semantic/style/names/links qualification, Telegram/server deployment,
  operator prices and paid launch. Structural/source-ID checks are not semantic proof.
- Next proposals and existing deliverables: [service portfolio](../docs/SERVICE_PORTFOLIO.md).
  Evidence: [translation report](REPORTS/2026-10-10-text-translation.md).

## Dedicated Telegram test-server qualification — 2026-10-10

- VERIFIED BASELINE: main a0ab15c includes Stars PR #32 and corrections #33–#35.
  Workflow 37992934577/job 114031500940 passed 696 tests, lint/format, migration/drift,
  Compose and all six actual non-root/network-disabled native worker qualifications.
- CONFIRMED GAP: All four runtime processes constructed production-only Telegram bots;
  the documented dedicated-test-environment Stars journeys could not select the test API.
- CURRENT SLICE: Explicit validated `TELEGRAM_API_ENVIRONMENT=production|test` and one
  provider bot factory, used by API/polling/worker/monitor for methods and file URLs.
  Production remains the default; no automatic endpoint fallback or Stars activation.
- Verification and boundaries: [test-server report](REPORTS/2026-10-10-telegram-test-environment.md).
- NEXT: On an identified isolated installation, execute the source-bound
  [Stars acceptance guide](../docs/STARS_ACCEPTANCE.md), then representative provider/native
  Office output, restart/recovery, support, alerts and off-server backup/restore journeys.
  These require private operator configuration; no live payment/deployment evidence claimed.

## CSV organization and review — 2026-10-09

- MERGED BASELINE: Main f4dc678 includes PR #30; workflow 37933829212 passed
  598 tests, migration/drift, Compose and all native network-disabled worker checks.
- CURRENT SLICE: Independent default-disabled csv_review turns pasted bounded CSV
  into Data/Source/Review Excel tables. Explicit delimiter and optional ASCII edge
  trimming; source IDs/numbers/dates remain text. No AI, deleted rows or inferred totals.
- Stable generated record references remain attached during sorting; review reports
  empty fields, full-record duplicates and changed source-column numbers.
- PASS: 31 local unit cases, lint/format/diff. Full lifecycle/worker qualification
  required on the exact published head before authorized merge; evidence on the PR.
- NOT RUN: Production deployment, Telegram/staging, representative Excel/mobile
  qualification and actual customer willingness to pay. Test-credit price only.
- Evidence: [CSV review](REPORTS/2026-10-09-csv-review.md).

## Current service expansion verification — 2026-10-09

- MERGED: CV formatting PR #28 at 00848f7; reviewed workflow 37927874220 and
  merged-main 37928968731 passed 545 tests/native Arabic-English CV worker checks.
- MERGED: Images PDF PR #29 at 30ec14c; reviewed workflow 37930551954 and
  merged-main 37931140860 passed 571 tests/native ordered pixel checks.
- MERGED PR #30 at f4dc678: Source-bound meeting-note categories, every source ID visible
  in review, mandatory approval before native Word/PDF; no invented fields/content.
- PASS: Local execution recovered; exact implementation head 27423a9 passes 73
  independent cases (CV 20/images 19/minutes 19/Word-PDF 12/governance 3), lint/format.
- PASS: Native AR/EN minute PDFs and both pages of synthetic receipt/review image PDF
  rendered and visually inspected. Earlier local unavailability is historical below.
- PASS: PR #30 final-head workflow 37933171985 and merged-main 37933829212
  passed 598 tests and all native worker checks. Live AI
  category accuracy, representative/native Office/mobile/Telegram/staging/server
  deployment and service activation remain separate NOT RUN gates. All new plugins
  default disabled; SAR values remain administrator-issued test credit.
- Service contracts and next priorities: docs/SERVICE_PORTFOLIO.md; see linked reports.

## Source-bound meeting note organization — 2026-10-09

- MERGED BASELINE: Images PDF PR #29, main `30ec14c`, reviewed
  workflow `37930551954` passed 571 tests and network-disabled ordered image checks.
- CURRENT SLICE: Independent disabled `meeting_minutes` classifies existing note
  IDs only; every note exactly once, no generated assignees/deadlines/free text.
- Customer reviews counts/sample categories before Word/PDF creation. Confirmation
  resumes without another AI call; source notes retained with traceable IDs.
- Prompt treats ambiguous/mixed notes as review. Category correctness still needs
  live-provider/customer acceptance; structural coverage is not semantic proof.
- Uses existing job AI budget/one repair, confirmation, abstract renderer and
  financial policy. 80 notes/12,000 characters, no audio/transcription or translation.
- Local execution unavailable: local/visual checks NOT RUN. Exact-head hosted
  lifecycle/native worker checks required before merge; enablement remains separate.
- Evidence: [meeting minutes](REPORTS/2026-10-09-meeting-minutes.md).

## Ordered images to PDF — 2026-10-09

- MERGED BASELINE: CV formatting PR #28, main `00848f7`, reviewed workflow
  `37927874220` passed 545 tests and native Arabic/English CV worker checks.
- CURRENT SLICE: Separate disabled-by-default `images_to_pdf`, one image per page
  in supplied order, A4 portrait/landscape/automatic orientation and 10 mm margins.
  EXIF orientation, alpha on white, no cropping/aspect distortion or new AI call.
- Limits: five files, 10 MiB each/20 MiB total, 20 million total decoded pixels,
  10 MiB output. Decode to pixels before embedding; original metadata omitted.
- Existing Telegram intake normalizes images to 1024 pixels and JPEG quality 88;
  this service does not restore source resolution or promise scan enhancement.
- New tests target exact embedded pixels/order/geometry, rotation/transparency,
  bounds/rejection, native lifecycle capture/release/ownership/cleanup/cached retry.
- Local execution became unavailable during this round. Local image tests/visual
  inspection NOT RUN; hosted exact-head checks required before merge and retained
  on the task PR. Representative/mobile/client/staging acceptance remains NOT RUN.
- Evidence: [images PDF report](REPORTS/2026-10-09-images-pdf.md).

## Valuable service expansion — 2026-10-09

- OWNER DECISION: Integrate useful services gradually; paid value means a clear usable
  deliverable, explicit source-preservation rules and source-bound quality checks.
  No blanket deployment/enablement or untested tool-installation claim.
- MERGED BASELINE: PR #27, main `081de25`; reviewed workflow `37925068485` and
  merged-main `37925579559` passed 516 tests and actual native worker image checks.
- CURRENT SLICE: Independent `cv_formatting` turns final structured career details into
  a classic single-column Word/PDF pair, with Arabic/English headings and no AI or
  invented qualifications. Generic optional Word alignment, default auto unchanged.
- PASS locally: 35 independent checks; native bilingual fixtures visually inspected,
  90-record multi-page CV retained. Hosted lifecycle/image checks required before merge.
- NEXT: Bounded ordered images-to-PDF with A4 fit/original aspect ratio and EXIF handling.
- Remaining premium candidates and qualification criteria: [service portfolio](../docs/SERVICE_PORTFOLIO.md).
- Evidence: [CV formatting](REPORTS/2026-10-09-cv-formatting.md).

## Native Word/PDF bundle — 2026-10-09

- MERGED BASELINE: PR #26 at `b1f86fe`; reviewed workflow `37920858118` and
  merged-main workflow `37921298499` passed 481 tests, migrations/drift, Compose
  and non-root worker image build with actual Arabic/English/mixed OCR.
- NEXT SLICE: Separate default-disabled `text_to_word_pdf` formats final text with
  the source-owned Word template and exports that same DOCX through LibreOffice.
  No AI calls, rewriting, translation, uploaded Office parsing or core service branches.
- Shared native capacity serializes OCR/export; per-request profile and temporary
  files, fixed headless export, CPU/address-space/output/wall limits and group cleanup.
- REPRODUCED/FIXED: Native PDF visually reversed an Arabic-adjacent ISO date despite
  correct text extraction. Existing date-direction formatting fixes the new renderer;
  an actual glyph-position regression test failed before and passed after the fix.
- PASS: 25 new independent cases plus existing OCR/architecture regressions: 61 cases;
  single-page Arabic/bilingual sample and all three pages of a 55-row table inspected.
- Full suite collects 516 tests. Exact-head hosted lifecycle/image checks required
  before merge; real Telegram, native Office and server deployment remain NOT RUN.
- Evidence: [Word/PDF bundle](REPORTS/2026-10-09-word-pdf-bundle.md).

## Local printed-text OCR — 2026-10-09

- MERGED BASELINE: PR #25 at `02d11c8`; exact-head workflow `37918022653`
  and merged-main workflow `37918332000` passed 439 tests and all existing gates.
- NEXT SLICE: Independent default-disabled local OCR plugin, injected document provider
  and worker-only Tesseract packages. No AI calls, translation or automatic fallback.
- Limits: five images/20 MiB total, existing 1024-pixel normalization; serialized
  subprocesses with CPU/memory/output/wall limits and cancellation cleanup.
- PASS: 33 local independent tests, including actual Arabic/English/mixed native OCR
  and exact English identifier/amount/date matching; full suite collects 481 tests.
- Hosted lifecycle, migration/drift, Compose and actual worker image checks required
  before merge. Representative images, Telegram staging and deployment NOT RUN.
- Evidence: [local OCR report](REPORTS/2026-10-09-local-ocr.md).

## Deterministic PDF utilities — 2026-10-09

- MERGED: PR #24 at `27d67a6`; exact-head workflow `37917138383` passed 406 tests,
  lint/format, migrations/drift and Compose. Template and structural gate in main.
- NEXT SLICE: Registry-discovered `pdf_tools` merges PDFs and extracts selected pages
  without AI, using the existing pypdf library. Native page text/images/geometry retained.
- Limits: five files, 10 MiB each/20 MiB total, 200 source pages; explicit source order.
  Forms/signatures unsupported. New service remains disabled until operator acceptance.
- No bot/core branches, dependency, migration, existing price or financial-policy change.
- PASS: 24 local independent cases and lint/format; 439 full tests collected. Hosted
  capture/release/ownership/retry checks required before merge; no deployment performed.
- Evidence: [PDF utilities](REPORTS/2026-10-09-pdf-tools.md).

## Document engines adoption — 2026-10-09

- OWNER DECISION: Adopt specialized deterministic tools and professional templates
  gradually, preserve clean registry-driven architecture and default professional output.
- FIRST SLICE: Reusable source-owned docxtpl Word template with escaped request values,
  native tables and existing Arabic/date handling; no additional provider calls.
- FIRST SLICE: Structural DOCX/XLSX/PPTX/PDF gate before storage/delivery, with generic
  failure/release lifecycle regression. No financial/intake/DB contract changes.
- PASS: 117 local database-independent checks, lint/format; 406 tests collected.
  Synthetic single-page and all three pages of 55-row Arabic output visually inspected.
- NOT RUN locally: Full DB/Redis CI, deployment, live provider and native Office acceptance.
- Remaining candidates and isolated-worker sequence: [document engines](../docs/DOCUMENT_ENGINES.md).
  See [template report](REPORTS/2026-10-09-document-templates.md). Only used dependencies
  are installed; approval of the direction does not imply all candidates are implemented.

## PDF Arabic numeric extraction — 2026-10-09

- FACT: A supplied one-page text PDF visually contains order 00123 and SAR 125.50;
  default extraction omits both with the project's locked pypdf 6.19.0.
- PASS: A generated synthetic Arabic/English regression fails on baseline and passes
  with bounded visitor-fragment collection and Arabic-presentation-form normalization.
- PASS: The supplied PDF retains its order, amount and date with the new extractor.
- FACT: PDF-to-Word version 3 invalidates older pending contracts while preserving
  administrator-owned enabled/price overrides. No new dependencies or schema migration.
- UNKNOWN: The exact real-provider reason for the earlier missing-information response.
  Provider success, native Word acceptance and production deployment remain NOT RUN.
- Hosted CI is recorded on the task PR separately from local unit verification.
- See REPORTS/2026-10-09-pdf-arabic-extraction.md.

Reconciled with live GitHub on 2026-10-08. This roadmap is not a production release approval.

## Current verified state

- FACT: Source of truth is n923760-rgb/telegram-services-platform, official branch main.
- FACT: PRs #1–#4 and #6 are merged: Compose CI setup, recovery/retention safeguards,
  text-to-PowerPoint, text-to-PDF and shared Office builder quality.
- FACT: PR #7 is merged at a8f70f7eb58d457dfefb4e378c5085e6fc9d3092:
  persistent Arabic/English menus, intake, support and delivery notices.
- PASS: Reviewed UX head f498413 passed 152 tests, lint, format, migrations, schema drift
  and Compose configuration in workflow 37575252712. Post-merge main workflow
  37575645208 also completed successfully.
- FACT: PR #5 is merged at a3aaf573238a497659bfa3137073185bf10b7340. PDF-to-Word
  is discovered, disabled by default, and rejects encrypted, unreadable, mixed and oversized
  input before an AI call. Original page-layout/image/table reconstruction is outside scope.
- PASS: Reviewed PDF-to-Word head a0cce87 passed 171 tests, lint/format, migrations,
  schema drift and Compose configuration in workflow 37576254914. Nineteen focused cases
  cover extraction, ownership/limits, credit release and cached delivery recovery.
- PASS: Local smoke used actual PDF parsing and DOCX reopening. Hosted integration evidence
  is retained in EVIDENCE/README.md separately from real-provider qualification.
- NOT RUN here: Container runtime and authenticated Telegram/provider journeys; no access to
  the operator's server or private configuration is available in this workspace.
- FACT: No production deployment or service enablement was performed in this review.
- Historical environment limitations in dated reports remain historical evidence, not the
  current hosted test result. See REPORTS/2026-10-07-pdf-to-word-review.md.

## Customer experience continuation — 2026-10-07

- FACT: Task branch adds persistent two-column navigation, owner-scoped paginated order
  history, localized state/time details, prompt steps and scoped cancellation.
- FACT: Menu/support/home navigation preserves drafts; language changes redraw the current
  question. Existing service-selection, payment and settlement contracts remain in place.
- PASS: Locked local install, lint/format/diff and collection of 203 tests (32 new cases).
- PASS: Task source d3d10b04 passed [hosted workflow 37659108407](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37659108407):
  203 tests, lint/format, migrations/drift and Compose configuration. The later evidence
  update changes documentation only; inspect its final-head workflow separately.
- NOT RUN: Authenticated Telegram/provider and deployment qualification.
- Evidence: [customer-navigation report](REPORTS/2026-10-07-customer-navigation.md).

## Direct document continuation — 2026-10-08

- FACT: Baseline main faab75a includes merged PR #9; post-merge workflow 37727678417 passed
  203 tests, lint/format, migrations/drift and Compose configuration.
- OPERATOR-REPORTED: Compose build succeeded, services healthy and migrations exited 0;
  the operator's `/health` response was HTTP 200 on 2026-10-08. No SSH access is available here.
- OPERATOR-REPORTED: Telegram screenshots show echo delivery, completed order history,
  persistent navigation and zero reserved credit. Real Office/PDF output quality and full
  before/after financial audit remain unqualified.
- FACT: Current task adds explicit direct Word/PDF modes without AI, a shared bounded input
  contract and pure per-request AI gating. Existing smart behavior, prices, ledger, general
  cost admission limits and cached-delivery rules are preserved. Plugin contracts become version 2.
- FACT: No dependency, database schema, new service, agent loop or workflow was added;
  no unused-code deletion was justified in this bounded inspection. Shared input validation
  replaces repeated parsing, and a duplicate import was removed.
- PASS: Local service tests and Word/PDF render inspection; final counts and limits in
  [the direct-document report](REPORTS/2026-10-08-direct-documents.md).
- PASS: Application/test source 798f023 passed [workflow 37771104090](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37771104090):
  240 tests, lint/format, migrations/drift and Compose configuration. Final evidence-only
  update CI must be inspected separately before merging PR #10.
- NOT RUN: New direct-mode server deployment/Telegram acceptance. This section is task
  evidence, not post-merge proof.

## Optional document title continuation — 2026-10-08

- OPERATOR-REPORTED: Main 67b46d1 deployed; clean source, healthy API/bot/worker,
  migrations exited 0 and `/health` returned `{"status":"ok"}`.
- FACT: Uploaded PDF sample is readable with correct title and leading-zero numbers.
  Uploaded Word repeats the whole body as its title; the file cannot prove how that title
  was entered. Uploaded Excel is one text column, not typed structured data.
- FACT: This bounded task makes direct Word/PDF titles optional with localized No title
  buttons and single-line validation; preserves strict smart-mode document schemas.
- FACT: No provider call, dependency, migration, price or financial policy change.
  Contracts increment to version 3; stale drafts restart and unprepared old jobs release.
- PASS: Local lint/format and 39 service tests; full integration evidence requires CI.
- NOT RUN: Updated server deployment, Telegram optional-title acceptance and financial audit.
- Excel specialization remains a separate next slice.

## Legacy snapshot startup repair — 2026-10-08

- OPERATOR-REPORTED FAIL: Main f325f75 runs API and migrations, but bot/worker repeatedly
  fail `registry.sync` with the unchanged-version input-contract guard. Worker teardown
  additionally raises `KeyError: bot` because startup failed before constructing the bot.
- FACT: Adding default `skip_key` and `single_line` to InputField changes every serialized
  plugin schema; fresh-database CI did not exercise pre-upgrade stored snapshots.
- FIX: Compare contracts after removing only these two explicit no-op defaults recursively.
  Preserve every other/unknown difference and the version-bump guard; sync retains admin
  settings and stores the current schema. Worker teardown closes only a constructed bot.
- CHECKS: Add legacy-snapshot upgrade, repeated sync, unchanged queued-order settlement,
  actual/unknown contract-change rejection and failed-startup teardown regression tests.
- NOT RUN: Repaired server deployment and Telegram acceptance. No DB/ledger rewrite,
  dependency, migration, service version or price change is required.

## Professional Word continuation — 2026-10-08

- OPERATOR-REPORTED: PR #12 deployment at 949e040 is healthy; migrations exited 0 and
  `/health` returned `{"status":"ok"}`. Untitled literal Word preserves the sample but
  the owner rejects mere text transfer as the professional service experience.
- FACT: This task adds a clearly labeled first-choice professional Word route: concise
  AI-proposed title, task-appropriate sections/lists and bounded editable native tables.
  Literal transfer remains explicit, title optional and without provider calls.
- FACT: Word/Excel contract becomes version 4; PDF stays 3. No dependency, migration,
  price, financial policy or new service changes. Existing generic lifecycle stays intact.
- PASS: 47 local service tests; Arabic/English single-page and 55-row five-page builder
  samples visually inspected with repeated headers, legible cells and page numbers.
  Samples use explicit plans, not a real AI provider; they do not prove factual fidelity.
- PASS: Application head 0e003c5 passed [hosted workflow 37805173177](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37805173177):
  268 tests, lint/format, migrations/drift and Compose configuration. Includes rich-table
  delivery/capture, bounded repair/failure release, literal/Excel regressions and version-3
  snapshot upgrade retaining admin settings. Inspect the final documentation-head check too.
- NOT RUN: New server deployment and live professional Word/source-fidelity acceptance.
  Excel quality improvements remain a later independent task.

## Automatic Word intake — 2026-10-08

- OWNER DECISION: Professional Word should be automatic; remove the additional mode/title
  questions. Preserve literal text on explicit request without searching phrases inside prose.
- FACT: Office version 5 asks only content and format. Exact Arabic/English first-line
  directive selects literal rendering without provider calls; only the directive is removed.
  The remaining body retains whitespace/lines/identifiers. Empty body fails before reservation.
- FACT: No bot/core branch, dependency, migration, rendering, price or financial-policy change.
  PDF retains version 3 and its existing explicit modes/optional title. Removed unused mode labels.
- PASS: 57 local service tests, lint/format/diff; 276 tests collected. Full hosted CI must pass
  before merge, including generic intake, default-provider gating, literal settlement/recovery,
  rich Word delivery and old version-3/4 snapshots retaining admin settings.
- NOT RUN: New server deployment and source-bound professional Word acceptance. The latest
  screenshot shows the PR #13 prompt, not a newly reviewed output document.

## Word date layout qualification — 2026-10-08

- FACT: Reviewed the owner's actual three-order report against the supplied test source.
  Names, IDs 00123–00125, amounts, dates, customer notes and required actions are retained;
  no total or third-order delivery deadline was invented. The report is one editable page.
- FAIL: ISO dates display in reversed order within Arabic prose; the narrow receipt-date
  column wraps each date onto two lines. Logical source date strings themselves are intact.
- FIX: Isolate date text runs and use invisible LTR boundary marks only in professional
  Word mode; literal/default builders add no characters. Date-bearing table columns gain
  a 2.7 cm minimum width within existing page margins. No date conversion/calculation.
- PASS: Local structural/date-fidelity tests and 57 service tests; visually confirmed the
  same report content with correct displayed dates and single-line date cells. All four
  pages of a 55-row date fixture were inspected: repeated headers, intact dates and IDs,
  no clipped rows, and no blank terminal page.
- FACT: No dependency, migration, contract version, price or financial-policy change.
  PR #14 main workflow 37809651597 was cancelled during setup, not a passed main check;
  its reviewed identical application head passed 276 tests in workflow 37809263650.
- NOT RUN: New server deployment, Microsoft Word/iPhone rendering and broad provider
  quality qualification. This one real output is evidence for this sample only.

## All-service output quality request — 2026-10-08

- OWNER REQUEST: Professional, native-editable Office outputs across the approved services.
  This supersedes the earlier deferral of Excel/PowerPoint inspection, not payment/deployment gates.
- FACT: Baseline main `25529b5` retains the recent Word/date improvements; main workflow
  `37813772656` passed. Operator reports `/health` ok, without a current source-bound output sample.
- IMPLEMENTED ON TASK BRANCH: First bounded slice upgrades Excel to a native table with visible
  title, typed formats, source missing/duplicate observations, safer precision/header handling
  and read/edit/save/reopen plus lifecycle regression tests. Legacy plans remain supported.
- NOT RUN: Live-provider, visual renderer and Microsoft Excel acceptance for this new slice.
- NEXT SLICES: PowerPoint readability/overflow and richer native layouts; PDF-to-Word reconstruction
  within approved scope; service-specific OCR/PDF fidelity qualification. Do not advertise
  unimplemented charts, original-layout reconstruction or guaranteed AI fidelity.
- Use [output quality gates](../docs/OUTPUT_QUALITY.md) for every service; preserve the existing
  [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md). Evidence and local limits:
  [Excel quality report](REPORTS/2026-10-08-excel-quality.md).

## PowerPoint quality round — 2026-10-08

- FACT: PR #16 is merged as `ac14b10`; main workflow `37822366757` passed 308 tests.
- MERGED PR #17: Native editable text/tables, readable bounded layouts, normal
  content on dense first/single slides and schema-level density checks using existing one-repair
  handling. Service contract version 2 retains administrator-owned price and enablement.
- PASS: Local lint/format and 35 focused builder/plugin/governance tests; 332 tests collected.
- FAIL / UNKNOWN: Artifact Tool import/render produced all three synthetic slides without
  clipping, but reversed Arabic word order and ignored the table RTL column flag. This renderer
  does not qualify Arabic output. Native PowerPoint behavior remains UNKNOWN, not a passing gate.
- PASS: Head `d94cbe5` workflow `37826017821` and merged main `76613b9` workflow
  `37827248529` passed 332 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live-provider fidelity and Microsoft PowerPoint edit/render acceptance.
  See [PowerPoint quality report](REPORTS/2026-10-08-pptx-quality.md) and PR #17's final CI evidence.

## PDF date rendering round — 2026-10-08

- FAIL: Poppler rendering confirms the existing PDF builder displays source `2026-10-08`
  as `08-10-2026` inside Arabic text, including headings. This is a rendering error.
- MERGED PR #18: Protect matched numeric date order only during bidi shaping, and use
  the same shaped text for width measurement. Dates remain literal, with no parsing,
  conversion, calendar inference or added formatting controls in delivered text.
- PASS: 29 focused local builder/PDF-plugin/governance tests, lint/format. Inspect every page
  of the corrected one-page mixed fixture and four-page 80-record fixture with Poppler.
- PASS: Head `77aba3a` workflow `37827978286` and merged main `b3deb01` workflow
  `37829349423` passed 340 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live-provider source fidelity, new server/iPhone viewer acceptance.
  See [PDF date report](REPORTS/2026-10-08-pdf-dates.md). No contract, version, dependency,
  payment, database or runtime changes are included in this rendering fix.

## PDF-to-Word mixed-content fidelity round — 2026-10-08

- FAIL REPRODUCED: Four real hybrid PDFs pass the old service because selectable text masks
  raster content: ordinary image, inline image, nested Form image and later mixed page.
- MERGED PR #19: Reject raster drawing instructions before AI/output without
  decoding image pixels. Follow invoked Forms with cycle/depth/instruction traversal limits;
  retain text-only Forms and allow unused image resources. Localized intake/error explain scope.
- FACT: Contract version 2; preserve admin price/enablement and generic cancellation/release
  for old pending version-1 orders. No new OCR, provider, database or dependency changes.
- PASS: 24 local helper/plugin/governance tests; hosted lifecycle tests must prove release,
  one notification, no AI/delivery, cleanup and old-order settlement. Full suite collects 355 tests.
- PASS: Head `de90211` workflow `37830310598` and merged main `6415e57` workflow
  `37831298533` passed 355 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Real provider/Word fidelity or deployment. This is a
  rejection safeguard, not image reconstruction or full-fidelity conversion qualification.
- Evidence: [mixed-content report](REPORTS/2026-10-08-pdf-word-image-fidelity.md).

## OCR translation numeric fidelity round — 2026-10-08

- FACT: The old translation model validates JSON/text length, but accepts changed amounts,
  dropped identifier zeros, missing/extra numbers and reformatted dates.
- MERGED PR #20: Request-local translation validation compares literal numeric
  tokens and their occurrence counts with the extracted text. Schema instructions preserve
  signs/separators/date notation/percentages and digit script; existing one-repair flow applies.
- FACT: Version 2; unchanged input fields, price/default gates, renderer, provider and financial
  policy. Old pending version-1 work releases; admin settings remain intact.
- PASS: 26 focused local schema/plugin/governance tests; 383 tests collected. Hosted cases
  cover repair, failure release, single capture, cost recording and cached TXT/DOCX delivery.
- PASS: Reviewed head `ea3b7d0` workflow `37832745093` and merged main `6ce0c5e`
  workflow `37862487540` passed 383 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live image/source fidelity, semantic translation and native Word acceptance.
  Matching numbers alone does not verify their associations, names, units or prose.
- Evidence: [OCR translation report](REPORTS/2026-10-08-ocr-translation-numbers.md).

## Excel filter interoperability round — 2026-10-09

- OPERATOR-REPORTED: Main `6ce0c5e` deployed with backup/migrations PASS, healthy application
  containers and `/health` ok. Actual uploaded XLSX retains the four synthetic source rows,
  IDs, dates, blank amount, zero and duplicate row, but Excel on iPhone requests repair and
  the owner reports recovery cannot open it. Native Excel acceptance is FAIL, not qualified.
- FACT: Both worksheet and native-table filters cover exactly the same range in the upload
  and current builder. Three new tests reproduce this filter-ownership defect before the fix.
- FIX ON TASK BRANCH: Remove only the overlapping worksheet filter; keep the native Records
  table and its filter. Existing values, formatting, RTL, print settings and freeze panes stay.
- INFERENCE: This known interop defect may explain the reported failure. Native iPhone
  opening/edit/save/reopen still must confirm the fix; no repaired-output claim is made.
- NOT RUN: Final hosted checks and post-fix native Excel/provider qualification.
- Evidence: [filter interoperability report](REPORTS/2026-10-09-excel-filter-ownership.md).

## Architecture and state owners

Use registry-driven plugins and generic bot intake. Purchases belong to orders, execution
attempts to jobs and credit authority to the immutable PostgreSQL ledger.
PostgreSQL owns durable dispatch/results/deletion recovery; Redis supplies queues and
short-lived coordination. Inject provider/storage interfaces and use typed file builders.
Keep specific service names out of core policy.

## Closed historical work

| Milestone | Retained result |
| --- | --- |
| Foundation and registry | Revised phase 1: 51 tests |
| Operations and financial recovery | Revised phase 2: 58 tests |
| Shared AI/file layers | Revised phase 3: 72 tests |
| Real services and complete recovery paths | Revised phase 4: 83 tests |
| Governance adaptation | Inspection complete; focused checks recorded in evidence index |

Details: [validation](../docs/VALIDATION.md),
[baseline](REPORTS/2026-10-04-governance-baseline.md), [evidence](EVIDENCE/README.md).

## Findings and release blockers

1. NOT RUN: Real source-bound Telegram/provider acceptance on a dedicated staging account.
2. NOT RUN here: Docker build/start/recovery and server-specific deployment qualification.
3. NOT RUN: Representative Arabic/English PDF extraction and live provider output quality.
4. UNKNOWN current provider rates/billing need operator configuration and reconciliation.
5. FACT SAR wallet credits remain test credits; separate direct Stars checkout is default-disabled and requires source-bound Telegram acceptance.
6. FACT external delivery is at least once; send/commit crashes can duplicate output.

## Ordered qualification gates

| Gate | Required proof / authority |
| --- | --- |
| Remote source | Verified target and write access; preserve existing initialization and verify the uploaded tree |
| Hosted checks | Run the existing workflow against the published source and inspect actual logs |
| Container staging | Build Compose, migrate, check health and test restart/recovery on an available machine |
| Private setup | Configure Telegram/AI credentials and rates on the operating machine |
| Real journeys | Echo first, then clear/unclear Arabic/English OCR and Word/Excel; inspect ledger/deletion |
| Operations | Verify alerts, reports, backup/restore and off-server copying in staging |
| Candidate freeze | Bind source SHA, artifact hash and retained evidence |
| Production decision | Explicit deployment authority and resolved digital-sales payment contract |

## Owner decisions and deferred work

Identify staging and configure secrets privately; retain remote/hosted evidence separately from deployment.
Keep payment gateways, dashboards, unapproved extra services, agent loops and n8n out of current scope.
Do not purchase infrastructure, merge, tag, release or deploy implicitly.

## Exact immediate next round

Owner's 2026-10-09 completion request authorizes the independent direct Stars V1 round.
Scope: existing registered services and generic customer/admin/payment/recovery flows.
See [design](../docs/STARS_DESIGN.md) and [acceptance](../docs/STARS_ACCEPTANCE.md).
Local lint/source checks and hosted PostgreSQL tests must pass before authorized merge.
Do not mark real Telegram purchase/refund, provider quality, or server deployment complete
without their actual evidence; future portfolio candidates remain separate work.

Verify the latest main workflow before using that source for runtime qualification.
Complete the Excel filter-ownership fix and inspect its source-bound hosted checks.
Retest the same synthetic source in native Excel before considering Excel qualified.
Qualify professional Word, Excel and PowerPoint against supplied source and native Office;
keep literal Word/PDF checks distinct. The all-service quality request supersedes the earlier
Excel/PowerPoint deferral. Continue PDF/OCR fidelity rounds within their approved contracts.
Run the [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md) on an available staging
server with a dedicated test account and operator-configured secrets. Use echo first, then
Office/PDF and clear/unclear OCR; inspect reservations, capture/release and file cleanup.
The operator must identify the installation and deployment method before runtime changes.
Keep real-provider quality and billing evidence separate from mocked integration checks.
Do not reopen completed phases without a confirmed finding or invent runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).

Hosted evidence and CI correction: [report](REPORTS/2026-10-04-compose-ci.md).
