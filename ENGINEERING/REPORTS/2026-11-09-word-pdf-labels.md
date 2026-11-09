# Word and PDF source labels and formatting notes

- FACT: live owner review found a repeated title and Required label in both outputs. A formatting instruction copied into the content field was retained as source text.
- CHANGE: v5 exposes optional bounded formatting_notes independently of content, with localized entry/review labels. Notes guide layout only; source segments keep complete ordered IDs and literal checks. Reject literal note leakage when the note is absent from source; paraphrase leakage still requires semantic/manual review. Direct mode rejects notes rather than silently ignoring them.
- CHANGE: after validation, represent an exact first-line title once in the generated title, when other content remains. Suppress a generated section heading equal to its first remaining source block after whitespace/trailing colon trimming. Keep the source block and all other repeated text.
- PASS locally: 31 unit tests; lint, format and whitespace checks.
- NOT RUN locally: PostgreSQL-backed journeys, hosted CI, rebuilt-worker/provider acceptance and final mobile rendering.
- No deployment or edits to uploaded customer files.
