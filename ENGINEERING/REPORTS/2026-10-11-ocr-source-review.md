# OCR source detail and automatic native review

## Source and authority

Owner authorized continuous verified implementation/merges, one customer outcome,
automatic AI review where needed and optional independent translation. Local/remote
main baseline 462e8b2f79fecfc9d7cfe961c5172dc197e0e323 was verified. Worktree isolated;
older unrelated pending work retained. No VPS credentials or production user tests.

## Findings and bounded fix

FACT: Default intake and native OCR each resized evidence to 1024px JPEG. Confident
native recognition bypassed the production AI quality gate. ImageToText v5 now opts
into validated original intake, native metadata-free PNG up to 2048px and sanitized
2048px JPEG for the adapter. Native confidence >=0.90 is a candidate, not certification:
production reviews source images and literal-transcription task before delivery.
One candidate correction and final review are allowed, maximum four provider calls;
existing accounted holds/caps/recovery and single customer price stay in force.
No arbitrary model downloads, dependency changes, activation or payment changes.
Native low confidence/classified failure retains existing AI fallback. Security,
invalid file, resource and timeout failures do not authorize outbound fallback.

## Qualification

PASS local: 23 focused gateway/source tests, ruff lint/format, diff whitespace and
three architecture gates. Native English 1800px numeric fixture reads exact original
text, confidence 0.9605, retaining leading zeros, decimal and date. New full DB tests
cover review costs, cached delivery without new calls, rejected review releasing
credit and v4 contract cancellation preserving administrator settings. Hosted
workflow/container qualification is required on the exact published head before merge.

Private operator-supplied samples were recovered for read-only testing, never added
to Git. English text bubble: native accepted at 0.961 and retained three expected
numeric tokens. Screen comparison: conservative native guard still rejects unclear
numeric text; AI fallback acceptance NOT RUN. Comparing JPEG evidence at 1024px vs
retained 1152px raised mean English-engine word confidence on that screen from
67.0 to 81.1; this is engine confidence, not measured transcription accuracy.
Arabic receipt/text samples cannot be qualified locally: installed native data here
is English/OSD only. Hosted Arabic synthetic fixtures are distinct evidence.

Initial hosted head 43b59ce: 1166 passed / 3 failed because three old intake
fixtures omitted the explicit preserve_image keyword. Updated fixtures assert it
is True, preserving their malformed-callback/draft-recovery assertions. No runtime
policy was weakened. Rerun full hosted workflow on the corrected head before merge.

## Limits and deployment

Same-model review can still accept wrong text. The uploaded comparisons are composites,
not original camera files; they do not establish restoration quality. No deblur,
dewarp, handwriting model or all-page visual review is claimed. No live provider,
Stars transaction, Telegram UI, throughput, actual costs or VPS deployment performed.
No selling-price change: review expense remains operator cost within existing caps.
After deployment, use new orders with Arabic/English files, small text, unclear
numbers and optional translation; inspect actual provider costs and final accuracy.
