# MASTER ENGINEERING BASELINE REPORT

Date: 2026-10-09 (Asia/Riyadh)
Project: Telegram Services Platform
Repository: n923760-rgb/telegram-services-platform
Official branch: main
Observed official HEAD: 6415e57da8cec22d198c4bd941d4ffa864dc3c98
Selected reference: f3ec2dcca8851d185c2fb0ab96214a6662e52c6c / 2.0.0-dev.1 (unreleased)
Mode: read-only existing-adoption session delta, retained during the later authorized documentation round.
Status: DRAFT_LIVE_VERIFICATION_REQUIRED

The existing [2026-10-04 baseline](2026-10-04-governance-baseline.md) and dated product
reports remain historical evidence. This record updates governance attribution and
applicable gaps; it does not replace the roadmap or qualify the product.

## A. Project identity
FACT: Public owner repository; GitHub reports main as default branch. Local clone
origin matches the canonical URL and Git confirms the observed official HEAD.

## B. Live repository state
FACT: Main is 6415e57da8cec22d198c4bd941d4ffa864dc3c98, tree a3daed90963d47863e596da8606eddb63747ef32.
Open project PR #20 addresses OCR translation numeric fidelity at ea3b7d09ebe338a6c9fce306ee20d6691e971dae.
Its changed files do not overlap this adoption slice. The central repository's
different PR #20 is merged; its main source is the selected reference above.

## C. Current canonical source
FACT: Existing application, dependency locks, migrations, CI and single roadmap
are retained. Historical SHAs in AGENTS.md and roadmap sections are checkpoints,
not the current source. Recheck official HEAD before publishing or merging.

## D. Existing repository governance
FACT: Root AGENTS.md defines plugin, financial, data, validation and Git boundaries.
No other scoped AGENTS.md was found in the inspected source. docs/GOVERNANCE.md
previously pinned reference 641e4f9e45da109257ba1f38752b94604c2e4531.
No source lock/profile existed; this branch proposes attribution records without
running bootstrap over the existing project.

## E. Build / release configuration
FACT: Python >=3.12,<3.13; uv.lock and requirements.lock are retained.
Compose and uv commands are prescribed in AGENTS.md. Signing/mobile tracks do not
apply to this backend. Release, deployment and paid-launch approval are NOT RUN.

## F. Application / system architecture map
FACT: Telegram and HTTP adapters, core settings/DB, wallet, orders, registry-driven
services, workers, providers, builders, files and operations remain separate.
This change introduces no runtime dependency, vendor integration or service.

## G. Authoritative state / ownership map
FACT: Project contracts assign durable orders, dispatch, results and financial
ledger to PostgreSQL; Redis supplies queue/coordination. Immutable signed ledger
entries own credit. Files/builders/providers retain their existing interfaces.
No ownership or financial rule changes are proposed.

## H. Feature / subsystem inventory
FACT: Existing echo, OCR/translation, Office/PDF and PDF-to-Word service contracts
are retained. Output scope and unresolved fidelity gates remain in docs/OUTPUT_QUALITY.md.
Plugin discovery is trusted executable code, not a sandbox.

## I. Platform / runtime contract
FACT: Arabic/English Telegram journeys, backend durable jobs and native-editable
Office outputs are applicable tracks. Native Office/provider acceptance is
separate from schema, file reopening, mocked delivery and HTTP health.

## J. Test inventory
FACT: Existing architecture gates inspect plugin imports, named service branches
and AGENTS.md length; integration tests require disposable *_test PostgreSQL.
The existing CI runs lint, format, migrations, pytest, drift and Compose checks.
No product behavior changes require new mirrored tests in this documentation round.

## K. CI / automation inventory
PASS: Main workflow 37831298533 completed successfully; its job and all validation
steps were inspected through GitHub. Central post-merge workflow 37860391490 passed.
FACT: The target main branch API reports unprotected; repository rulesets returned
an empty list at inspection. Required branch protection is a remaining adoption gap.
No workflow or settings are changed in this slice.

## L. Security / privacy boundaries
FACT: Secrets remain untracked and customer content excluded from Git/reports.
Project authority explicitly treats customer instructions as data, requires JSON
validation and rejects unsafe input. The update preserves these restrictions.
No credentials, provider rates or customer data were accessed.

## M. Current evidence coverage
The sanitized [source/CI observation](../EVIDENCE/2026-10-09-governance-source-review.json)
retains source identity, relevant open PR, run/job statuses and protection findings.
This is selected API metadata, not complete execution logs or independent attestation.
Local attribution checks are retained separately in the adoption-check artifact.
Hosted checks do not establish real-provider or VPS acceptance.

## N. Risk / gap ledger
Project risk: HIGH for credit, customer files, provider budgets and delivery.
Current task: LIGHT, bounded documentation/source attribution.
BLOCKED: VPS Codex agent-tool execution qualification remains unresolved after
direct sandbox probes and two-version smoke attempts; no additional model probe runs here.
NOT RUN here: Current-source staging/Telegram, native Office/provider acceptance,
paid-launch, release and production deployment.
UNKNOWN: Current installation restore/off-server backup evidence.
FACT: Target main has no protection/ruleset in the inspected snapshot.

## O. Proposed repository authority model
Owner instructions and root AGENTS.md govern this project; reviewed pinned reference
guidance remains subordinate. A source lock cannot authenticate an owner or grant
permission. Self-review is labeled as such, not independent review.

## P. Proposed PROJECT-SOURCES model
Retain PROJECT-SOURCES.md as navigation and existing paths. New lock/profile and
this report are linked from docs/GOVERNANCE.md; no competing resource map is created.

## Q. Proposed canonical roadmap state
Keep ENGINEERING/MASTER_ROADMAP.md unchanged to avoid the active OCR task's owned
area. In its next reconciliation, attach this review and resolve source-dependent
protection/runtime gaps. Do not rewrite historical milestone evidence as current fact.

## R. Engineering lab plan
FACT: This round has local Git/Python, a repository connector and hosted CI inspection.
The operator VPS, private credentials, DB/Redis and native Office are not connected
for acceptance here. Use the existing AGENTS.md/CI and docs/OPERATIONS.md contracts;
verify available capacity and runtime before any heavy or deployment work.

## S. Required lab toolchain
Python 3.12 and locked uv dependencies; affected project checks remain unchanged.
Reference validation uses the selected reference's pinned requirements.
No global tool update or OS/security policy change is part of this task.

## T. Controller / executor operating model
The current agent performs source inspection, bounded execution and self-review.
Actual local checks and GitHub runs count as their own evidence; they do not qualify
the VPS AI executor or constitute independent human review.

## U. Evidence / report storage model
Reuse ENGINEERING/REPORTS and ENGINEERING/EVIDENCE. Keep sanitized metadata and
actual command output, exact source/environment and sensitivity classification.
For new automated packets, select the approved task and manifest independently;
bind task bytes/hash and validate with the pinned v2 contracts. Historical evidence
keeps its original contract. Concise human LIGHT reviews remain permitted.

## V. Owner-protected decisions
Owner explicitly authorized merge of central governance PR #20 and continuation.
This new project adoption PR is prepared for review; that central approval is not
a standing grant for unrelated product PRs, payments, settings, deployment or release.
No root instructions, roadmap, app code, migrations, private setup or published tag changes.

## W. Exact next engineering round
Review this adapted source lock/profile and exact-head CI before accepting the update.
Address target branch-protection and applicable qualification gaps as separate bounded
actions. Resume source-bound real Telegram/provider/native Office acceptance using
the existing guides when the operator's staging environment is available.
Adoption stays DRAFT until its applicable gates are actually satisfied.
