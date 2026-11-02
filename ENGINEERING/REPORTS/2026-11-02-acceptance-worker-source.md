# Acceptance must verify effective worker source

## Finding and baseline

FACT on verified main `a46fc6f`: the acceptance wrapper records checkout HEAD and
mounts two acceptance modules over the configured worker image. It never compares
the rest of that image with the checkout. A successful report can therefore come
from older service/builders/provider code. The existing wrapper comment explicitly
identifies `source-commit.txt` as checkout provenance only.

The owner's supplied archive retains valid artifact hashes and its reported test
results. Those hashes do not establish which worker source generated the artifacts.
Earlier descriptions of that archive as source-bound should be read with this limit.

## Change

- Build a stdlib-only manifest of clean tracked application/migration files plus
  lock/build declarations. Include paths and SHA-256 values, never `.env`, customer
  files, provider credentials or configuration values.
- Verify the effective selected worker in a no-input preflight before acceptance
  DB creation, backup creation or provider calls. Reject stale/missing/extra files,
  unsafe paths and symlinks; ignore ordinary Python bytecode cache directories.
- Preserve existing non-root identity and two read-only acceptance mounts, adding
  the checker and a temporary read-only manifest. These explicit module overlays
  are included in effective-source verification; do not claim an unmodified image.
- Recheck inside the actual execution container before configuration, migrations,
  seeding or provider activity. Initial preflight mismatch creates no test DB.
  A mismatch detected only on the second container stops before migration/provider
  calls; the already-created disposable DB remains for diagnosis under existing rules.
- Archive the manifest and preflight verification summary. Remove temporary local
  manifest/summary files on normal success/failure exits. Production pause state,
  acceptance case list, financial budgets and service contracts remain unchanged.
- Add hosted focused unit checks and real document-worker image/source verification
  before the existing native image qualification.

## Limits

This is trusted-operator source comparison, not cryptographic build attestation or
an adversarial sandbox. It does not prove installed Python dependencies match their
declarations, operating-system packages, native binaries, real provider/client quality,
or that a different long-running production container uses this image. A Git SHA
describes the checkout; effective mounted files are the actual verified execution scope.

## Verification

- PASS locally: 19 manifest/wrapper tests cover matching files, source/lock changes,
  missing/extra source, file/directory symlinks, unsafe paths, source privacy, dirty
  checkouts, unreadable mounts, source-probe failure and no DB creation on preflight
  failure. Wrapper tests use fake Docker; they are not real container evidence.
- PASS locally: whole-repository lint/format, shell syntax and diff whitespace.
- PASS locally: 135 selected acceptance/source/wrapper/readiness/output/delivery
  and architecture tests in the broader regression selection (includes the 19 above).
- NOT RUN locally: Docker build/run, PostgreSQL acceptance and actual provider calls.
  Hosted CI must check the real built worker before merge and the selected deployment
  must pass this check before the next actual editing acceptance run.
