# Independent proofreading and rewriting — 2026-10-10

## Baseline and authority

FACT: main 68ae143 contains independent translation PR #37. Its post-merge workflow
38069092755/job 114262659938 passed 740 tests and all native worker gates; actual
logs reviewed. Owner accepted continuing the proposed proofreading/rewriting service.
Existing continuous merge authority applies after verification. No server access used.

## Contract and integration

Independent registry plugin `text_editing` v1, disabled by default, AI required.
SAR 3.00 is a test-credit default, not a commercial quote or Stars price. DB-owned
price/enabled overrides and Stars terms/pricing remain unchanged.

Pasted Arabic/English text stays in its original language. Proofreading corrects
spelling/grammar/punctuation minimally; rewriting improves clarity in formal,
business or casual tone. Generic conditional intake asks tone only for rewriting.
No new Telegram/core/payment policy branches or provider/library dependencies.

Input is normalized to LF and bounded to 12000 characters, 80 nonempty source lines;
blank/control/surrogate/noncharacter input rejected. Source JSON includes integer
segment IDs. Request-local strict validation requires each ID once, no new fields,
no within-segment newlines, printable text and total output <=24000 characters.
Numeric token multisets and recognized email/HTTP(S)/www URL token multisets must
match per line. Match values are not exposed in JSON Schema or validation errors.
URL detection is lexical, whitespace-delimited and conservative (adjacent punctuation
is part of the URL token); it is not a URL parser or a guarantee of every contact form.
Source ordering and original blank lines are reconstructed deterministically.

Returns draft text plus owned UTF-8 revision.txt. Uses existing provider abstraction,
one repair and budget accounting. Existing runner persists delivery before retry,
captures once, releases failures and cleans artifacts; no content logged by plugin.
This service does not send letters/emails to recipients or translate uploaded files.

## Verification

Targeted unit tests cover malformed/missing/duplicate/unknown/coerced IDs, numeric
changes/movement, output limits, input admission, request isolation, recognized contact
changes/addition/omission/movement, Arabic and English owned TXT output, missing/failed
provider, conditional tone intake and architecture. Real PostgreSQL lifecycle tests
cover both modes, AR/EN, repair, one capture, rejection/release, contact failure,
file-save failure, cached retry without another provider call and disabled-AI admission.

Local DB/Redis/native worker runtime unavailable: full hosted CI required; local
DB-independent checks use --noconftest explicitly, without modifying shared fixtures.
PASS LOCAL: ruff check/format, diff check and 82 DB-independent checks (33 new
editing cases plus translation/OCR numeric/architecture regressions). Full collection
finds 785 tests, including 12 new real-DB lifecycle cases.

Final exact-head full-suite, lint/format, migration/drift, Compose and native-worker
results are recorded on the PR before merge. No live-provider result is fabricated.

## Live acceptance still required

Before enablement, an isolated configured provider and Telegram installation must
qualify at least: Arabic spelling/hamza and English grammar; unchanged already-correct
text; minimal proofreading vs each rewriting tone; mixed AR/EN; names and qualifications;
negations ("لم أوافق"/"I did not agree"), requests vs commitments, uncertain dates,
repeated amounts/zero/leading zeros, emails/URLs with query strings, instruction-like
source content, long/blank-line text, invalid response after one repair and delivery retry.
Compare source and draft manually for every factual claim and sentence. Structural
checks cannot prove meaning/style/language or prevent every hallucinated word.
Real paid launch additionally requires owner prices/Stars terms and acceptance gates.
