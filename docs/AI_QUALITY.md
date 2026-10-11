# Automatic source-based AI quality review

Production AI extraction automatically reviews each validated candidate against the
original source, images, task and schema. Customers do not choose engines or review
modes. Existing plugin validators still run; this does not bypass numeric, source-ID
or consent restrictions. Reviewer verdicts contain only strict acceptance and a
bounded list of issue codes: meaning, omission, unsupported content, numbers,
language, instructions. No customer source or prose findings are logged.

One creation repair is allowed, shared between invalid JSON/schema and content
rejection. A repaired candidate is schema-validated and reviewed against the original
source again. A second rejection/invalid candidate stops the order. First review can
repair its own invalid verdict once; a final review has no retry. Maximum five
provider calls per extraction, not a recursive agent loop. Accepted initial output
normally needs two calls. Every call uses existing global/user/job holds and settled
usage; uncertainty retains exposure. Review/correction costs belong to the operator,
within existing caps; customer price and payment contract are unchanged.

An unavailable review or exhausted budget prevents unreviewed delivery. Cached
prepared results are replayed without new generation/review/billing. Existing job
transport retries remain governed by the worker; the per-extraction bound is not a
new guarantee of one provider request per order. A terminal failure releases test
credit or queues the existing authenticated Stars refund process. Refund completion
still requires Telegram confirmation.

## Scope and practical limits

This is a same-provider/model content check, not an independent accuracy guarantee.
It covers production AI.extract paths: translation, editing, summary selection,
Office/PDF/PowerPoint plans, meeting minutes, optional table labels and AI OCR
fallback and native OCR candidates when production AI is configured. Deterministic
PDF/image tools, image restoration and direct CV formatting are outside this gate. It reviews content
before rendering, not all rendered pages/slides. No services are activated here.

Real Arabic/English/provider acceptance must measure meaning, names, negation,
source fidelity, false acceptance/rejection, cost headroom and latency before
claiming a commercial quality improvement. Mocked provider tests establish control
flow and monetary lifecycle only. All-page visual review and stronger image
restoration engines remain separate development slices.

Future design services should use supplied brand/assets, editable text layouts and
bounded revisions, then validate rendered Arabic/English composition. This gate
does not register or promise a design service.


## Native OCR source review

Image-to-text v5 keeps the validated received image in owner-bound storage. Native
OCR reads metadata-free PNG evidence up to 2048px per side, without another lossy
JPEG encoding. AI receives metadata-free 2048px JPEG evidence matching the existing
adapter contract. Input byte/decoded-pixel/security checks and native subprocess
limits remain. Images sent as Telegram files retain more source detail than photos;
this cannot recover detail already removed by Telegram or the camera.

A native candidate accepted at confidence >=0.90 is still reviewed against the
image in production. One successful review call is typical; at most four calls
(one verdict schema repair, one candidate correction, one final verdict). Each call
uses the existing usage ledger/caps. Failed final review stops delivery. Weak native
results continue through the bounded AI extraction/review path. Translation remains
a separately confirmed optional service. Native offline qualification with no AI
is a provider test, not evidence of the production review path.

No model/provider cost defaults, selling prices, activation or payment mode change.
Version 5 is a real intake contract change: unprepared older jobs settle/cancel via
existing recovery rules; prepared results are replayed. Operator acceptance must
verify cost headroom for image review and Arabic/English numeric fidelity.
