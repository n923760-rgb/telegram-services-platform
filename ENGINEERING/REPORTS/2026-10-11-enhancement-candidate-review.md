# Enhancement candidates and automatic quality gate

Owner requests professional automatic AI support and improvement of unsatisfactory
image outputs. Baseline main 5ecde1426cfa81490e0fc1ba0f06cda8467b0d7b verified; worktree isolated.

## Findings and change

FACT: Current contrast processing can worsen a photographed screen. On a private
operator comparison sample, English-engine mean word confidence was 80.98 for
received JPEG vs 66.14 for the contrast result. This is not transcription accuracy.
Blind sharpening of that result reached 69.65, still below the source; therefore
no unconditional sharpening was adopted. No customer images/content committed.

Enhancement v3 creates contrast and separate bounded RGB/luminance sharpening
candidates. Sharpening changes channel values by at most 13 intensity units including
rounding, preserves geometry and does not synthesize text. AI receives sanitized
JPEG evidence in fixed source/contrast/sharpen order; strict choice none/contrast/sharpen
uses the existing bounded source-aware AI extraction/review and cost holds. No
freeform explanation or customer engine selection. A none choice fails before
saving outputs and uses existing credit release/Stars refund queue policy.
No-improvement input rejection is excluded from the circuit-breaker failure count,
with a generic error-code regression (no named-service policy branch).
Original received bytes retained in successful delivery. Cached outputs replay
without another image build, review or expense. AI now required; version bumped
to 3, no migration/default activation/price/provider-rate changes.

## Evidence and limits

PASS local: five focused selection/rejection/missing-provider/sharpen tests;
six direct existing native/service cases, three architecture gates, lint/format.
Known synthetic Gaussian blur: sharpen candidate reduces pixel error by over 15%
against its clear reference, with bounded change. This is not proof on arbitrary
blurred photographs. Hosted tests add failed selection credit release/file cleanup,
review costs and old-contract settings preservation; exact-head full workflow is
required before merge. Native offline tests do not qualify AI visual judgement.

NOT RUN: real AI candidate acceptance/rejection, Arabic receipts, handwriting/QR
readability, real billing/latency/VPS/Telegram. Same-model review can miss defects;
there is no guaranteed blur removal or accuracy. Review expense remains operator
cost under configured job/user/global budgets, separate from manual selling prices.
The gate may decline photographs lacking a reliable improvement.

## External engine review

Primary sources checked 2026-10-11:
- https://github.com/ZZZHANG-jx/DocRes : specialized deblur/dewarp/shadow restoration,
  separately downloaded weights. Its requirements pin torch 1.11+cu113 and numpy
  1.21.6: https://github.com/ZZZHANG-jx/DocRes/blob/master/requirements.txt .
  Inference: cannot drop this dependency set into the existing Python 3.12 worker;
  qualify a separate pinned runtime/model provenance and resources first.
- https://www.paddleocr.ai/main/en/version3.x/module_usage/text_image_unwarping.html :
  UVDoc rectification supports CPU. Rectification addresses geometric distortion,
  not a general promise to restore lost text. Model not installed/qualified here.

No heavyweight restoration engine or weights were installed. Future integration
must compare representative original files against current outputs and preserve
numeric/stamp fidelity before being advertised. No deployment or activation claim.
