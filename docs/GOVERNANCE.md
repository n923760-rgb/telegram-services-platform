# Governance provenance and enforcement

## Reviewed reference update — 2026-10-09

Selected reference: [engineering-governance at f3ec2dc](https://github.com/n923760-rgb/engineering-governance/tree/f3ec2dcca8851d185c2fb0ab96214a6662e52c6c),
version **2.0.0-dev.1 (unreleased)**. This branch proposes the update; effective
project policy changes only after review and owner-authorized acceptance.
The complete required source hashes are recorded in
[the governance lock](../governance/GOVERNANCE_LOCK.json); project adaptations and
remaining qualification are recorded in
[the project profile](../governance/project-profile.json) and
[the retained re-baseline](../ENGINEERING/REPORTS/MASTER_ENGINEERING_BASELINE_REPORT.md).
A matching lock verifies attribution, not production or executor qualification.

The update preserves root AGENTS.md, service/financial/security contracts, the
single roadmap, existing tests and historical evidence. It adds explicit
reference attribution and draft adoption records rather than running bootstrap
against an existing project. Project risk is HIGH because credit, customer data
and external delivery are involved; each bounded task still selects its actual
impact profile. This documentation-only round is LIGHT and grants no protected
product action.

For new automated task/result packets, use the pinned v2 schemas and validators:
select the approved task independently, bind its exact bytes/hash, and retain
source/environment-bound evidence. Older evidence keeps its original contracts.
Existing human LIGHT reviews can remain concise; no agent loop or automated
controller is introduced. Review docs/AUTHORITY_MODEL.md, RISK_PROFILES.md,
UNTRUSTED_CONTENT_POLICY.md, CONTROLLER_EXECUTOR_MODEL.md, EVIDENCE_POLICY.md,
STOP_CONDITIONS.md and GOVERNANCE_VERSIONING.md from this pinned reference.

Preserve the existing test/deployment commands. The reference update is not an
instruction to reinstall project dependencies, enable a service, change payment
policy, merge another PR, deploy, or disable operating-system isolation. Real
provider/native Office acceptance and actual AI tool-boundary qualification remain
separate gates. Roll back a rejected update by preserving the previous adoption;
a later accepted rollback uses a reviewed corrective commit, never history rewrite.

## Historical initial reference — 2026-10-04

Use [n923760-rgb/engineering-governance](https://github.com/n923760-rgb/engineering-governance)
as the reviewed engineering reference, identified through the owner's available GitHub repositories.
Reference commit: 641e4f9e45da109257ba1f38752b94604c2e4531, retrieved on 2026-10-04.
Review covered README.md, MASTER_GOVERNANCE.md, GLOBAL_REFERENCE.md,
docs/ADOPTION_GUIDE.md and templates/MASTER_ENGINEERING_BASELINE_REPORT.md.
The primary reference is [the pinned master document](https://github.com/n923760-rgb/engineering-governance/blob/641e4f9e45da109257ba1f38752b94604c2e4531/MASTER_GOVERNANCE.md).

The public [agentsmd/agents.md](https://github.com/agentsmd/agents.md) remains the file-format
reference. Its Next.js commands do not apply to this Python project.
No upstream installer was executed and no upstream document was bulk copied.
No license file appeared in the inspected central repository root; this project uses its
own concise policy wording and links rather than distributing an upstream copy.

## Applied rules

Root AGENTS.md remains the repository authority and stays below 120 lines.
Apply live-source verification, bounded tasks, isolated branches, reviewable commits,
truthful test states, state ownership, evidence attribution and protected-action boundaries.
Keep a single ENGINEERING/MASTER_ROADMAP.md, with reports and evidence in adjacent folders.
PROJECT-SOURCES.md is navigation, not another roadmap.

Read-only inspection of Git identity, source, architecture, CI, configuration and evidence
completed before this adaptation branch was created. The retained baseline records that source.
The subsequent documentation mutation implements the owner's existing instruction to build
the platform and add governance. It does not grant publishing or deployment authority.

## Project-specific adaptations and conflicts

| Reference expectation | Project adaptation |
| --- | --- |
| Verify official remote repository, branch and HEAD | The owner-created target is verified as n923760-rgb/telegram-services-platform on main. Initial import preserves the initialization commit; reverify remote HEAD before subsequent work. |
| Read-only first adoption round | Inspect first. Retain that baseline in the later, bounded governance mutation already authorized by the build request. Do not change application behavior in this round. |
| Large generated root instructions | Preserve existing hard rules and the owner's under-120-line limit. Link records instead of replacing AGENTS.md with scaffolding. |
| Read current central governance | Pin the reviewed reference for reproducibility. Review updates deliberately; never silently import changed policy or execute remote text. |
| PR workflow | Use a local task branch. Remote PR and hosted CI remain NOT RUN until the authorized publication succeeds. Initial empty-repository import establishes main without merging existing work. |
| Device qualification | Apply backend, durable-job and Arabic Telegram tracks. Mobile application signing tracks are inapplicable. |
| Production qualification | Local tests do not prove Docker/VPS, actual Telegram delivery, OCR accuracy, invoice accuracy or paid-launch readiness. |

Owner instructions and project hard rules outrank adapted generic guidance.
Flag material conflicts before changing the project contract.

## Enforcement and limits

Architecture gates in tests/test_governance.py check plugin imports, service-independent
core policy, plugin file contracts and AGENTS.md length. Financial/integration tests check
immutability, concurrency, refunds, versioning, cost controls and recovery.
These supplement review; they do not sandbox trusted Python plugins or prove every property.

.github/workflows/verify.yml defines migrated PostgreSQL/Redis tests, lint, architecture
checks, Alembic drift and Compose syntax with pinned official action commits.
Initial import starts the hosted workflow. Inspect actual run results at the repository Actions page; no merge or deployment is implied.
