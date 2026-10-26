# Documentation update log

## 2026-10-26

- Implemented E1: retained rule snapshots with pinned batch versions, legacy backfill, authenticated deterministic help, unknown/unsupported/inconsistent snapshot refusals, and a scoped illustrative category breakdown. No official policy review or LLM is claimed.
- E1 validation: 50 backend tests passed in 27.62 s, including a populated upgrade preserving old reports. Frontend lint/types/tests/build passed (six tests); expanded browser journey passed in 4.3 s after replacing an ambiguous count selector introduced by category helper text. Used a separate synthetic smoke database; no development database reset.

- Began execution with E0. Added explicit capability checks to core HTTP dependencies, sign-in, scoped repositories, and mutation services. Unsupported/future roles can no longer inherit cross-institution access from a null institution ID. Existing institution isolation and officer read-only behaviour remain covered.
- Baseline: 37 backend tests passed. E0: eight focused permission tests passed, then all 45 backend tests passed in 23.87 s. No frontend/runtime dependency or database schema changed in E0.
- Incorporated the user's constraints into E3/E5/E6: corrected staged rows leave current held-work counts without changing historical reports; identity promotions resolve person/digest locks before enrolment locks; audit genesis works without an external seed step and new features supply separate test keys. E5/E6 can be scheduled as isolated tested slices if E3 is delayed.

- Added Document 11 from the supplied feature notes: phased execution for resolution/diff, rule provenance/categories, overlap review, audit integrity, and consent/QR. Defined a short-deadline Release A and a later complete Release B, human tasks, proposed contracts, fixture checks, and a bounded first implementation prompt.
- Adjusted unsafe/incomplete task-card assumptions: explicit role scoping before new users, staged-row correction targets, exact encrypted proposals and stale-batch checks, overlapping category dimensions, concurrency-safe overlap reconciliation, dedicated audit-head/key, and private consent request addressing with token-safe QR delivery.
- Added an entirely unchecked extension checklist and cross-links. The user-supplied official/adoption assertions have no exact source links/dates and remain unverified. This update changes documentation only; no new application feature or test result is claimed.
- Planning-document validation passed: 11 concept documents have valid draft metadata, 52 local documentation links resolve, E0–E8 are present, and all extension implementation checkboxes remain unchecked. No application tests were run for this planning-only change.

- Added an APAAR ecosystem, adoption, UI-research, and differentiation document. Inspected three public peer projects at pinned revisions; substantial overlap means imports, dashboards, QR/consent, AI help, and even transactional/idempotent ingestion are not established exclusive features.
- Recommended a focused correction workflow and measurable staff outcomes. Clearly separated current local core, proposed extensions, publisher claims, and research hypotheses. No application features or policy rules changed.
- Official government, search, and news sites were blocked by the environment network policy. No current official UI, national adoption figure, or publicity-failure claim was verified. Saved required research-domain additions as an environment draft; access still needs an actual settings change and successful retry.
- Documentation checks passed: ten concept files have valid draft metadata, 42 local documentation links resolve, and 11 pinned peer file references exist in the inspected Git objects. No application tests were rerun for this documentation-only update.

- Fixed the reported local browser/API origin mismatch. Local mode now recognises the exact localhost/127.0.0.1 pair on port 5173 even for existing `.env` files; new configuration lists both. Hosted origin lists remain exact. All five focused preflight/rejection tests passed; style checks passed. User confirmed a healthy local API/database response and that using localhost resolved the browser issue.

- Fixed the reported native Windows setup failure: npm's PowerShell wrapper accessed a missing `$MyInvocation.Statement` property under the helpers' strict mode. Initialization and frontend startup now explicitly call `npm.cmd`; the prerequisite check and Windows manual commands use the command shims too.
- The fix preserves existing `.env` settings, dependency locks, and strict error checking. Native Windows execution is still not available in this cloud machine; the report confirms the original failure, not an end-to-end Windows pass.

## 2026-10-25

- Implemented and verified the local Python/PostgreSQL/React core: scoped accounts, CSV review, transactional commit/correction, lifecycle, intake reporting, history, and audit correlation. Final evidence is recorded in the checklist.
- Added native Windows PowerShell setup and PostgreSQL helper; Ubuntu/WSL is not required. Added timezone data for Windows. Windows execution itself remains unverified.
- User confirmed commit identity `hanesh-g <haneshgourishetti@gmail.com>`. Corrected the initial documentation commit locally and added repository instructions/identity setup for future work.
- Added database integrity constraints, safe structured error/request logs, meaningful migration/concurrency/rollback/privacy tests, frontend checks, real-browser smoke, and a CI configuration. Remote CI/hosting execution remains pending.
- Rotated a disposable local database password after a sandbox-denied test exposed it in diagnostics. Added connection preflight sanitization, short test tracebacks, and safe parameter IDs. No credential is committed.
- Verified local database outage/recovery, retained records/decryption, and a 500-row HTTP dry run. Local timing is not a hosted capacity claim.

- AI created the problem statement, technical design, detailed feature specification, phased implementation plan, evidence checklist, and AI development playbook.
- Adapted the source guide from Node/Express to Python/FastAPI and a bounded synchronous demo. Kept PostgreSQL and the person/enrolment distinction.
- Set proposed core scope to F01–F11; separated optional consent verification, overlap review, and source-linked help from the release gate.
- Resolved the source guide's invalid-ID counting conflict: identity-only issues warn and remain countable; structural failures stay held and are reported separately.
- User supplied the Knowledge Catalog repository. AI inspected its migration notice and the canonical Open Knowledge Format v0.2 repository. Added pinned-source assessment and this OKF document bundle. No producer/LLM runtime was installed.
- At the original documentation-only stage, application tasks remained unchecked. Later entries above record the actual implementation evidence; no official registry access, hosting pass, or human policy review is claimed.
- Document-only validation passed: seven concept files have parseable OKF metadata; 21 local document links resolve; F01–F16 are present; no implementation checkbox is marked complete. This is not application validation.
