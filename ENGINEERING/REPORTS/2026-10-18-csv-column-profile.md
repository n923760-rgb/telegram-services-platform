# Source-owned CSV column summaries

Baseline: official main 40aa7fac2394533d96b1b1a2b0cdb4ff9c9b5137. Owner authorizes continuing development and tested merging, with one production deployment after improvements. No server action; unrelated governance PR #21 remains untouched.

## Customer result and exact counting policy

CSV review v3 keeps Data, Source, row-level Review and optional Similarities, adding a compact Columns sheet for all original columns. Each row has the original column number, exact source heading, Data heading after existing heading normalization, nonempty cells, empty cells, distinct nonempty values and edge-trimmed cells. The generated record-reference column is excluded.

Counts use Data values after the selected existing whitespace rule. Empty means exactly an empty string: preserved spaces, NBSP, NULL, N/A and nan are not guessed as empty. Distinct uses exact case-sensitive equality; numeric-looking text such as 0 and 00 remains distinct. Duplicate records remain included. Each column's filled plus blank count equals the source row count; blank/trimmed totals reconcile with Review. No inferred types, conversions, deletion, grouping, formulas or automatic edits.

Customer headings in the new sheet are explicit text cells, including formula-like prefixes; calculated counters remain native integer cells. Existing header/filter tables, frozen/repeated headings, wrapping and AR/EN direction are reused. The AR/EN notice explains the rules and that counts are a static creation-time snapshot, not recalculating spreadsheet formulas. The customer preview discloses the new sheet.

## Compatibility and boundaries

The output contract increments csv_review from v2 to v3. Same inputs, one review.xlsx artifact, administrator-owned prices/activation, source values/order/record references and optional lexical similarity rules/limits. No AI provider construction/cost, financial policy, dependency, migration or production change. Existing version guards release unprepared historical requests and replay prepared historical workbooks without appending a new sheet or rebuilding them. Both legacy v1 and v2 paths are covered; administrator overrides remain intact.

## Qualification

PASS LOCALLY: 69 focused native profile/CSV/similarity/whole-word wrapping tests, three architecture gates, global Ruff lint/format and diff. New cases cover both languages with/without similarity, expected full column counts, native integer/text types, stable column references, exact headings, case/NBSP/whitespace/zero semantics, formula/URL/macro exclusion, missing-value words and the maximum supported 20 columns by 500 empty records. Initial regression assertions expecting the previous sheet list were updated to the new explicit contract; existing value/formula/source checks remain.

Hosted lifecycle additions/updates check Columns in successful zero-AI delivery and cached retry, preserve failure/release/cleanup checks, and exercise prepared/unprepared v2 upgrade with administrator prices retained. The cached fixture is a historical three-sheet workbook and must replay unchanged without service execution. Existing v1 cancellation coverage now targets v3. Non-root/network-disabled worker qualification adds bilingual native count/table assertions; all earlier checks remain required. Full exact-head PostgreSQL/Redis/native-worker CI is required before merge. Docker is unavailable locally; no local container qualification claim.

## Limits

Literal counts do not establish business correctness, identify semantic missing values, infer column types or certify every Excel/mobile viewer. Counts intentionally remain static after customer edits; Data and Source retain the original editable values and references for further review. No new live Telegram/mobile/provider qualification or production deployment is claimed.
