# Arabic contact prose in Excel service outputs

Date: 2026-10-21 (Asia/Riyadh). Official baseline:
`9abc34efe57c116a462c414d8468f4a65b80da6e`.

## Finding and change

FACT: A real workbook containing Arabic column headings and the note "يرجى
التواصل عبر" followed by a long ASCII email reopens with an LTR worksheet,
left-aligned note and readingOrder=1. Contact characters overwhelm the existing
dominant-script detector. Source Excel also forces every ASCII-leading source
chunk to LTR, even if the remaining prose is Arabic.

CHANGE: Reuse the existing Word identifier matcher to ignore numeric dates and
ASCII email/URL tokens only when detecting Excel reading direction. Preserve the
literal cell values. Apply the same detection to Source Excel's worksheet and
source-text cell alignment/order. English prose and standalone identifiers remain
LTR; Arabic prose retains RTL even when an ASCII contact precedes it.

The shared Excel builder supplies three public service paths:

| Service path | Affected output | Evidence |
| --- | --- | --- |
| Text to Office, Excel | Data and Source | Exact contact/source/reference values, source prefixed by ASCII contact, editable save/reopen and per-cell order |
| CSV review | Data and Source plus shared review sheets | Literal original rows, exact counts and stable source-record references |
| PDF tables to Excel | Data and Source sheets | Literal extracted rows, stable T/R references and no formula execution |

Word and PowerPoint source already have contact-aware direction handling. This
round reuses their existing recognition rule in Excel; it does not change those
builders or claim a new all-service visual/live-provider qualification.

No service-specific core branches, schema/version, source normalization, values,
formulas, column widths, row heights, source label language, prices, activation,
provider/financial policy, dependency, migration or deployment changes. Existing
prepared files replay unchanged; new workbook generation gets the style fix.

## Checks and limits

PASS LOCALLY: 93 focused Excel/source/CSV/PDF-heading tests, including 25 new cases.
The new cases reopen actual XLSX bytes across all four builder entry points in
both languages, with long emails/HTTPS/www links, original literals and refs,
English-dominant prose, Arabic-digit dates, no formulas/hyperlinks and editable
save/reopen. These are native file structure/style checks, not Excel UI rendering.

PASS: 26 existing Excel quality/filter assertions in an isolated DB-free harness,
including typed dates/numbers/percentages, zero/null/duplicates, precision rejection,
1,000-row preservation, native filter ownership and edit/reopen. Three executable
architecture gates, global lint/format/diff and embedded worker Python syntax pass.
Counts overlap and should not be added as a whole-suite count.

PASS LOCALLY: Two new source-workbook native-worker assertions in AR/EN. Use only
existing runtime dependencies. Require the full hosted DB suite, migrations and
non-root/network-off worker qualification on this candidate before merge.

Local PostgreSQL, native Excel/mobile UI and live provider output are not qualified
by these checks. Direction still follows the remaining dominant prose; this is
not language identification or content rewriting. Workbook cells stay editable.
