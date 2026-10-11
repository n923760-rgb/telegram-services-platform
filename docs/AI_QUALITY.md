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
fallback. Native OCR accepted locally, deterministic PDF/image tools, image
restoration and direct CV formatting are outside this gate. It reviews content
before rendering, not all rendered pages/slides. No services are activated here.

Real Arabic/English/provider acceptance must measure meaning, names, negation,
source fidelity, false acceptance/rejection, cost headroom and latency before
claiming a commercial quality improvement. Mocked provider tests establish control
flow and monetary lifecycle only. All-page visual review and stronger image
restoration engines remain separate development slices.

Future design services should use supplied brand/assets, editable text layouts and
bounded revisions, then validate rendered Arabic/English composition. This gate
does not register or promise a design service.
