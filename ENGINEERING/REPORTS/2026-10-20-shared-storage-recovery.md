# Shared file-save failure recovery

## Source and confirmed problem

FACT: Official main 88f98b18f0d313911d9e84a4ffa1d7fcc85218b2 includes
#110. LocalStorage is used for customer uploads and generated service artifacts.
Fault injection reproduces partial/full `.tmp` files left after write/rename
failure. They consume the owner's file/byte quota and can block a retry.
The six new tests before the fix produced five failures and one pass.

CHANGE: While holding the existing owner quota lock, remove the temporary file
and empty destination directory on write/rename exceptions, including catchable
interruptions. Cleanup errors preserve the original exception. Existing age-based
retention can recover surviving temporary files if deletion was unavailable.
Keep successful files, owner isolation and quota serialization unchanged.

## Portfolio scope

The shared fix applies whenever these services save uploads/results. There is no
plugin schema/output change and no version bump. The existing synthetic acceptance
plan covers all 16 public services in 29 cases; checking that plan is not execution
of live provider acceptance. Refresh stale capability descriptions to current source.

| Service | Version | Existing output boundary retained |
| --- | --- | --- |
| csv_review | 3 | Literal CSV workbook and review/column sheets |
| cv_formatting | 7 | Source-bound Arabic/English/bilingual Word/PDF |
| document_image_enhancement | 3 | Selected PNG and comparison |
| image_to_text | 6 | Original recognized text and long TXT/Word exports |
| images_to_pdf | 3 | Explicit image order and bounded PDF |
| meeting_minutes | 4 | Complete classification review and Word/PDF |
| pdf_tables_excel | 4 | Reviewed source tables and literal workbook |
| pdf_to_word | 5 | Static text PDF conversion; reject interactive content |
| pdf_tools | 3 | Ordered merge, extraction and explicit rotation |
| text_editing | 2 | Edited text, revision and deterministic change report |
| text_summary | 3 | Numbered point references in chat/TXT |
| text_to_office | 8 | Explicit Word mode or source-bound Excel |
| text_to_pdf | 4 | Literal or source-checked smart PDF |
| text_to_pptx | 6 | Exact requested count and contact-aware direction |
| text_to_word_pdf | 3 | Selected Word/PDF/both and prepared visual review |
| text_translation | 2 | Per-line source-token bounds and retained blank lines |

## Verification and limits

PASS LOCALLY: Six new fault-injection cases cover partial writes, failed renames,
catchable interruptions, retry at an exact quota, owner isolation, cleanup failure
and retention fallback. Broader portfolio/source/output checks pass: 485 tests
including the six new cases. Seven additional existing quota tests pass without
the unavailable database fixture. Architecture gates, lint, formatting and diff
checks pass. Complete hosted PostgreSQL/worker qualification is required before
merge; record its source-bound results in the PR.

No additional AI calls, dependencies, migrations, prices/activation, provider pause,
financial-policy changes or production actions. Deployment remains one later batch.
NOT RUN: live Telegram/provider, native mobile and server-specific acceptance.
Limits: best-effort cleanup only, not crash-proof storage or a multi-file transaction;
SIGKILL/power loss still relies on retention. Semantic quality of every service is
not established by shared storage or structural tests.
