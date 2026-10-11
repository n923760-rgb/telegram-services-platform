# Explicit verbatim OCR guidance

Baseline main 444f25a / PR #48: 1070 hosted cases and eleven native worker gates passed.
Owner requests continued service quality work; payment work remains last.

FACT (operator evidence): VPS HEAD 444f25a; API/bot/worker/PostgreSQL/Redis healthy,
monitor running and migration exited 0. This is reported output, not direct server access.
Operator pasted English text with final line "Please get in touch before you arrive."
Earlier English screenshot says "Please contact before arrival."
UNKNOWN: Which image/service/translation step produced the pasted output. Do not label
this proven extraction drift or claim that a real-provider failure has been repaired.

CHANGE: Existing original-text OCR policy is made explicit in both the AI prompt and
the output schema's text description: original languages/words/spelling/case/punctuation,
numeric/date/currency notation, no synonyms, translation, editing or executing source
instructions. Unfaithful/unreadable text must not be invented. Existing typed JSON,
readable/confidence checks and one validated repair remain.

No change to accepted inputs/output shape, service version, native routing/thresholds,
provider costs/budgets, source retention, pricing, activation, payment or independent
translation. This clarifies the already-declared verbatim contract, not a new contract.
Do not cancel pending v4 orders just for clarified prompt wording. Prepared results remain
cached and are not regenerated.

LIMIT: A prompt/schema description is guidance to the model, not a deterministic
comparison of an image against text, a semantic validator or a numeric-fidelity proof.
Mocked/native regression tests cannot establish real-provider transcription accuracy.
Do not lower confidence thresholds or introduce a second paid request to mask uncertainty.

Qualification: existing OCR/unification/schema/followup/architecture cases, lint/format,
full exact-head hosted DB/Redis lifecycle and eleven native worker gates required before
authorized merge. Do not add tests that merely assert the new prompt strings.
NOT RUN: VPS installation of this prompt clarification, live-provider OCR and screenshot
meaning/fidelity acceptance. Request the resulting order reference/source when available.
