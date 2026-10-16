# Live acceptance output review and targeted diagnostics

## Authority and source

- OWNER AUTHORITY: Review the uploaded all-service results and continue existing service quality work. Live synthetic testing was authorized without waiting for historical invoice reconciliation.
- BASELINE: Official main 5c859803259d0b973d9fc2b5f33a604058381ac7 verified before mutation. Operator ran #84 ops modules over the previously deployed #83 worker. This is not evidence of a #84 production rebuild.
- EVIDENCE: Original private results ZIP SHA-256 `9510fee5985a45851ffbcca7ffb71a07ba6cd28cc15b39e359c94439c81fcb3f`, 751468 bytes. All 40 captured artifact hashes match report.json. Raw archive, synthetic outputs and provider request IDs are not committed.

## Observed outcome

FACT: 27/28 cases completed across all 16 public services, 41 provider calls, all 41 holds settled, zero remaining active orders and zero reserved test credit. Calculated usage totals SAR 0.253417; SAR 1.979355 is the cumulative conservative call-bound allowance used, not the bill. No recorded output-limit breach. Operator confirmed production pause remains true. Historical unknown exposure is untouched.

FACT: Single-language English CV failed with provider_invalid after three calls. Its third call returned 8192 output tokens, equal to the requested cap. The successful bilingual CV also used one 8192-token call. Equality is allowed and is not a cap breach.

UNKNOWN: The original report contains no generation/review stage, JSON validation category, finish reason or raw output. Three calls alone do not distinguish creation repair, invalid review JSON or semantic rejection. Reaching the cap does not prove truncation. The exact CV defect cannot be reconstructed from this archive; do not weaken fidelity validation or increase retries/caps on that evidence.

## Native and content review

Read all text responses, Word paragraphs/tables, spreadsheet values/types and slide text. Rendered all 14 supplied PDF pages, all nine Word export pages, all eleven Calc print pages and the one PowerPoint slide; inspected image enhancement outputs. Spreadsheet artifact previews were cross-checked with native Calc because the preview importer displayed text identifiers as numbers. Stored values and Calc retain 00123/00017 and 125.50.

| Service | Supplied evidence | Quality finding / remaining boundary |
| --- | --- | --- |
| CSV review | Text identifiers, literal formula-like value, duplicate/source audit | Data retained; only edge trimming applied. Small English fixture, no broad cleaning certification. |
| CV | Arabic and bilingual native pairs; English standalone failure | Clear single-column layout and fresh English page; restrained/basic visual hierarchy. Short fixture cannot qualify dense CV pagination or all profiles. Prioritize reproducible English failure, then richer design samples. |
| Document enhancement | Received/enhanced/comparison images | Text preserved and shading lighter; visible residual bands. Not restoration proof for blur, perspective or handwriting. |
| OCR | English and mixed-language responses | Fixture identifiers/date transcribed correctly. Mixed input is synthetic printed text, not a real Arabic scan. |
| Images to PDF | Two pages | Ordered images retained without clipping in supplied samples. |
| Meeting minutes | Arabic/English headings and action register | Reference, assignee and deadline preserved. Arabic option retains English source prose under Arabic headings by current source-preserving contract; not automatic translation. |
| PDF tables to Excel | Direct and proposed-heading workbooks | Cells, source rows, leading zeros and literal decimals retained. Original header stays as a data row under generated headings; header promotion would need explicit provenance-aware design. |
| PDF to Word | Native editable document | Text/identifiers retained, but original grid becomes paragraphs. Current text conversion does not reconstruct editable table/layout. |
| PDF tools | Extract and merged pages | Expected page content/count present. Synthetic merge uses identical source PDFs and does not qualify distinct-document ordering. |
| Text editing | Proofread and formal rewrite | Meaning, identifiers and payment negation preserved. Short fixture only. |
| Summary | Short summary and source references | Essential payment status and amount retained. Long-document coverage not tested. |
| Word/Excel creation | Direct Word, smart Word, smart Excel | Negative payment status retained; Excel typed amount/source references correct. Small layouts readable. Domain label proposals still require review. |
| Text PDF | Direct and smart | Literal direct text retained; smart headings/grouping readable. Short English fixture only. |
| PowerPoint | One slide | Readable title/bullets, identifiers/negation retained. One slide is insufficient evidence for long decks, dense Arabic text or richer design. |
| Word and PDF | Direct and smart pairs | Readable paired output, identifiers/negation retained. No dense pagination proof. |
| Translation | Arabic/English response files | Arabic translation preserves negation/numbers. English case source is already English, so it does not qualify Arabic-to-English translation. |

No missing glyphs or overlapping content observed in the reviewed native samples. These bounded observations are not universal mobile, semantic, ATS or invoice certification.

## Bounded change

- Optional exact-case selection in the existing fresh isolated runner/wrapper; no names retains all 28 cases. Unknown/duplicate selections fail rather than silently skipping them.
- Isolated-only DiagnosticAI observes the existing gateway's original schema/repair/review path. It records call number, generation/review stage, fixed validation categories and typed semantic verdict codes, with no content/messages/locations/prompts/custom error strings. The exact schema sent and original validated return type remain unchanged.
- Report calculated usage separately from conservative exposure bounds. No production AI gateway, service contract/version, template, retry count, provider cap, budget, ledger, admin gate, price, dependency or migration change.
- Targeted rerun example: `bash scripts/service-acceptance.sh cv_en`. Fresh synthetic DB and private outputs remain mandatory; production stays paused. New execution NOT RUN here.

## Validation

PASS LOCALLY: 21 focused pure acceptance/architecture checks, including exact schema preservation, bounded repair, semantic rejection distinction, no-content diagnostics and selection guards; full lint/format/diff and Bash syntax. PostgreSQL lifecycle and native full regression require hosted workflow before merge. Original live run was operator-performed; this change has no new real-provider result yet.
