# Images-to-PDF source quality

Owner authority: continue the approved quality-first project review; preserve customer
source details, automatic internal tools, manual sale pricing and independent provider costs.
Baseline: verified local/remote main f288f7a (PR #52); separate uncommitted AI review/profile
work is preserved in its existing worktree and is not included in this change.

## Findings and change

- FACT: Image PDF builder preserved decoded pixels, but ordinary Telegram admission
  resized images to 1024px and encoded JPEG before the builder received them.
- CHANGE: ImagesToPdf v2 opts into existing exact validated received-byte intake.
  EXIF rotation, metadata-free output, transparency composition, page order and aspect
  fit remain builder-owned. Advise customers to upload images as files: Telegram photo
  compression cannot be reversed by preserving the bytes received from its API.
- RESOURCE BOUND: Full-size generation uses an injected document renderer and a private
  POSIX child with 512MiB address-space, 25s CPU, 10MiB file and 30s elapsed limits.
  It shares one per-worker native slot; the event loop is not blocked by image work.
  Existing per-file/aggregate bytes, decoded pixels, output and storage limits remain.
  This is resource isolation, not a security sandbox or server capacity guarantee.
- COMPATIBILITY: Real input contract change bumps v1 to v2. Registry preserves enabled,
  SAR test price and Stars price overrides. Unprepared old-version orders use existing
  cancellation/release/refund policy; already persisted PDFs replay without rebuilding.
- No AI/vendor/model installation, pricing, Stars activation, schema migration or
  native dependency change. No claim that this removes blur or corrects document geometry.

## Qualification

- Local PASS: 28 images-PDF service/builder cases on final code, including actual
  intake-to-native-PDF high-resolution PNG/JPEG/WEBP pixel fidelity and failure/cancellation
  temporary-source/capacity cleanup. Lint/format/whitespace PASS. Local evidence is separate
  from hosted financial lifecycle and native worker qualification.
- Hosted required: complete lifecycle suite, migration drift, lint/format, Compose build,
  non-root network-disabled document worker, including actual high-resolution native
  renderer pixels. Added upgrade/cache lifecycle checks require disposable DB/Redis.
- NOT RUN here: production deployment, Telegram/mobile real source acceptance, paid
  purchase/refund, VPS peak memory/load and general image restoration acceptance.

Do not enable services or modify owner pricing during rollout. Retain the preupdate
database/source/settings backup and inspect migration exit and service health afterwards.
