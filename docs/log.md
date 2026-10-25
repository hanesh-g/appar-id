# Documentation update log

## 2026-10-26

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
