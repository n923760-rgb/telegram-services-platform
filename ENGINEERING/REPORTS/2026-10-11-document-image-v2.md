# Automatic document image enhancement v2

## Problem and scope

Owner requests stronger document image enhancement after reviewing a weak side-by-side screen photograph. Baseline main 47aee095c04965e46f2aa1c9768d2fcea41bc817. The attachment is an existing comparison, not a raw source; it was inspected privately, never committed or used as an acceptance fixture. Production activation state remains operator-owned.

FACT: Old Telegram intake resized images to 1024px and encoded JPEG before storage; old builder repeated normalization and only applied CLAHE. Preserving source bytes inside the old plugin did not recover upstream normalization loss.

## Change

Document enhancement v2 asks for one image, automatically chooses conservative bounded processing, and delivers enhanced PNG, comparison PNG, then the exact received source. No AI or engine question. Bright uneven paper uses bounded illumination correction (gain <=1.6) with dark foreground filled before background estimation to avoid text/stamp halos; detected high-frequency texture receives a blended bilateral filter; blended luminance CLAHE retains LAB color channels. No crop, geometry correction, thresholding, sharpening or invented characters. Colors are retained rather than deliberately removed, not guaranteed colorimetric identity.

Generic trusted InputField.preserve_image defaults false, only valid for image fields. Intake validates actual bytes under existing size/decode/format/storage/owner limits before preserving exact Telegram-received bytes and detecting the actual format. Other plugins retain 1024px JPEG normalization. Registry comparison ignores only the known false default, retaining real/unknown changes and version-bump requirements.

Builder decodes EXIF-corrected RGB from source without an intermediate JPEG, strips metadata from processed images, never upscales, bounds processing to 2048px longest side. Comparison is bounded to 1024px per panel. The separately returned source retains received bytes/metadata. Telegram can compress photos upstream; prompt recommends file upload. PNG outputs each remain <=10MiB, decoded input <=20 million pixels, existing owner storage quotas/cleanup remain.

## Compatibility and qualification

Version 2 records the real intake/execution change. Admin enabled/price values remain; queued incompatible v1 cancels/releases using existing policy. Already prepared v1 results replay without rebuilding/capture duplication. Historical source snapshots missing only no-op metadata still synchronize unchanged. No dependency/migration/default activation/payment changes.

PASS local: ruff, formatting, diff checks; 28 pure unit/intake/governance/normalization cases; English native OCR on shaded synthetic invoice retains exact leading-zero identifier, decimal and date before/after. The synthetic blank-paper illumination spread decreased >40%, blue stamp stayed colored, paper near text avoided bright halos, random noise standard deviation decreased >10%. EXIF rotation, metadata removal, no upscaling/2048 output, 1024 comparison panels, corrupt/foreign files, quota cleanup tested. A single 2048-square synthetic build took 1.004s in this workspace; this is not a throughput or peak-memory guarantee.

Hosted required: complete PostgreSQL/Redis lifecycle, dispatcher one-question confirmation with preservation flag, registry real-change rejection and upgrade/refund compatibility, cached retry; existing eleven native worker gates plus a twelfth automatic illumination/color/mixed numeric OCR gate in actual non-root network-disabled worker. Exact-head hosted evidence belongs in the PR after execution; it is not inferred from local checks.

NOT RUN locally: Arabic trained data, Docker worker, PostgreSQL/Redis suite. NOT RUN: updated VPS/mobile/source-photo/real customer/provider acceptance, faint handwriting, general OCR improvements, moire removal, production load. Threads are not a sandbox or CPU/memory quota. Bounds increase per-job pixel work; review representative raw sources and operator load before broad activation. Synthetic OCR tests establish those fixtures only, not general semantic fidelity. No screen-photo recovery promise.

References: OpenCV official [filtering](https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html), [CLAHE](https://docs.opencv.org/4.x/d6/db6/classcv_1_1CLAHE.html), Pillow [EXIF transpose](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose).
