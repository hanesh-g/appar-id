---
type: Delivery Checklist
title: Progress checklist
description: Track implementation gates and executed evidence without invented completion.
tags: [apaar, progress, testing, release]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-25T17:11:45Z"}
sources:
  - resource: 03-feature-specification.md
  - resource: 04-implementation-phases.md
---

# 05 — Progress checklist

## Current state

Documentation has been prepared. **Application progress is not yet verified.** All implementation boxes begin unchecked. No application tests or deployment checks have run as part of document creation.

Use `[x]` only with current evidence. Use an evidence path, commit, test result, or deployed check in the final column. Record blocked work in the blocker table, rather than marking it done. CORE must pass before the demo is described as ready.

## Phase gates

| Gate | State | Evidence / decision |
|---|---|---|
| P0 — Core and contracts adopted | Pending human review | Proposed baseline exists in this pack. |
| P1 — Local and hosted skeleton | Not started | — |
| P2 — Scoped users and data | Not started | — |
| P3 — Upload and dry run | Not started | — |
| P4 — Safe commit and correction | Not started | — |
| P5 — Reports and history | Not started | — |
| P6 — Deployed release gate | Not started | — |
| P7 — Optional extensions | Not selected | — |

## P0 — Inputs and human decisions

- [ ] HUMAN: Confirm official SIH statement and submission constraints.
- [ ] SHARED: Adopt core scope F01–F11; rank optional features.
- [ ] HUMAN: Confirm synthetic-only data and demo labels.
- [ ] SHARED: Confirm intake metric and warning/held-row policy.
- [ ] HUMAN: Select database provider and hosting plans/costs.
- [ ] HUMAN: Provide authorised account access and enter required values securely.
- [ ] SHARED: Adopt OKF document context; keep the reference agent out of the core runtime.

## P1 — Reproducible foundation

- [ ] AI: Python/Node pins and compatible locked dependencies.
- [ ] AI: Environment-name template contains no secrets.
- [ ] AI: PostgreSQL, migration command, API, and frontend start locally.
- [ ] AI: Database-ready health check succeeds and fails correctly.
- [ ] AI: Early hosted frontend reaches hosted backend/database.
- [ ] AI: Nested frontend URL loads directly.
- [ ] AI: Actual setup/start/check commands recorded.

## P2 — Access and data safety · F01/F02

- [ ] AI: Migrations succeed against a fresh PostgreSQL database.
- [ ] AI: Idempotent seed creates two institution users and an officer.
- [ ] AI: Valid login works; bad/expired/inactive credentials fail.
- [ ] AI: Passwords hashed; tokens constrained; secret fields excluded from responses.
- [ ] AI: Foreign institution list/detail/edit/export/batch access fails.
- [ ] AI: Programme validation, uniqueness, intake edit, and audit work.
- [ ] AI: Sensitive fields encrypt/decrypt; ciphertext tampering is rejected.
- [ ] HUMAN: Role views and demo credential distribution reviewed.

## P3 — Upload and review · F03/F04/F05

- [ ] AI: Template matches the documented CSV contract.
- [ ] AI: File/row limits are enforced during bounded parsing.
- [ ] AI: Empty, malformed, wrong-header, duplicate-key, unknown-programme, and bad-date cases fail clearly.
- [ ] AI: Request idempotency returns the original batch; changed content conflicts.
- [ ] AI: Known identity fixture produces exact expected states and reasons.
- [ ] AI: Missing/invalid identity is a warning, not a structural block.
- [ ] AI: Outage results are pending, not invalid.
- [ ] AI: Dry run writes no main enrolments.
- [ ] AI: Issue counts, fields, next actions, and intake preview are correct.
- [ ] AI: Authenticated CSV export is scoped, non-cacheable, and formula-safe.
- [ ] HUMAN: Correction instructions and mock labels make sense to a user.

## P4 — Save and correct · F06/F09

- [ ] AI: `commit_valid` saves acceptable rows and holds errors.
- [ ] AI: `all_or_nothing` refuses structural errors; identity-only warnings remain allowed.
- [ ] AI: Commit writes records/history/audit/result atomically.
- [ ] AI: Repeat commit causes no mutation.
- [ ] AI: Same students in a new batch do not duplicate enrolments.
- [ ] AI: Changed correction updates once; unchanged rows are no-ops.
- [ ] AI: Stale preview/new conflicts produce a clear refusal or refreshed result.
- [ ] AI: Concurrent attempts respect locks/constraints.
- [ ] AI: Forced mid-transaction failure rolls back all associated changes.
- [ ] AI: Recovery retry updates only eligible outage-pending rows and audits changes.
- [ ] AI: Identity reassignment/uniqueness conflict cannot silently merge people.
- [ ] HUMAN: End-to-end correction flow reviewed.

## P5 — Results and accountability · F07/F08/F10

- [ ] AI: Record list/detail and history are scoped and paginated.
- [ ] AI: Lifecycle dates validate; stale edit returns `409`.
- [ ] AI: Withdrawal changes active intake and preserves history.
- [ ] AI: 65-admission fixture produces 65 active, 5 missing, 5 excess.
- [ ] AI: Repeated batches/corrections do not inflate dashboard totals.
- [ ] AI: Held candidates are deduplicated; unassignable raw rows are labelled separately.
- [ ] AI: Empty/loading/error states are real, not seeded visual placeholders.
- [ ] AI: Audit writes are transactional and contain no personal values/tokens.
- [ ] HUMAN: Report language avoids unsupported official-compliance claims.

## P6 — Release gate · F11

- [ ] AI: Backend rule/API/integration suite passed with nonzero test counts.
- [ ] AI: Frontend typecheck/lint/relevant tests/build passed.
- [ ] AI: Browser core smoke passed against real API responses.
- [ ] AI: Clean-database migration and double-seed passed.
- [ ] AI: Frozen-lockfile installation reproduced.
- [ ] AI: Advertised maximum file tested on the actual hosting plan; timing recorded.
- [ ] AI: Hosted login/upload/commit/correction/dashboard/denial checks passed.
- [ ] AI: Exact CORS origins, HTTPS, database TLS, and frontend API URL checked.
- [ ] AI: API restart preserves records and decryption capability.
- [ ] AI: No dependency on ephemeral uploaded files or in-memory jobs.
- [ ] AI: Guarded demo-reset instructions tested on disposable database only.
- [ ] HUMAN: Actual hosting suspension/expiry/cost limitations checked.
- [ ] HUMAN: Secrets and published demo-account exposure reviewed.
- [ ] SHARED: Known limitations recorded; no claim of real registry integration.
- [ ] HUMAN: Demo rehearsal and backup recording completed.

## NEXT gates — select explicitly

- [ ] F12: Student/verifier scopes, approved fields, purpose, expiry, revocation, token redaction, and wrong-user denial all pass before a QR endpoint is exposed.
- [ ] F13: Overlap rules have human-confirmed assumptions; historical intervals and valid transfers are tested; review is not automatic fraud classification.
- [ ] F14: Approved sources/citations, no personal data, no write access, prompt-injection checks, timeouts, and model-off fallback pass.

No unchecked NEXT feature blocks a CORE-only release. Do not present an incomplete extension as delivered.

## Test fixtures and expected results

| Fixture | Construction | Required result |
|---|---|---|
| `identity-cases.csv` | 6 unique, structurally valid rows: active matching ID; absent ID; malformed ID; unknown format-valid ID; inactive ID; active ID with wrong DOB. | 1 VERIFIED, 1 MISSING, 3 INVALID, 1 PENDING_CHECK; 0 structural blocks; 5 affected rows with identity warnings. |
| Same fixture, mock outage | No caching; format checks still run; mock registry unavailable for all format-valid IDs. | 1 MISSING, 1 INVALID-format, 4 PENDING_CHECK-unavailable; no false VERIFIED result. Recovery retry does not retry the missing/invalid-format rows. |
| `intake-65.csv` | 65 distinct active admissions in one 60-seat programme; 60 mock-verified, 5 missing IDs. | 65 committed; 5 missing; 5 above configured intake. |
| `corrections.csv` | Known existing canonical key with one permitted change; include unchanged keys. | Count unchanged; changed record increments version; unchanged records do not. |
| `structural-errors.csv` | Known invalid date, unknown programme, missing required value; each on a distinct row. | 3 blocked rows; no accidental main-record writes during dry run. |
| `duplicate-keys.csv` | Two rows with the same canonical key. | Structural failure/clear duplicate issue; no double counting. |
| `cross-institution` | A attempts to use B's batch, record, report, and export identifiers. | No private record data exposed; forbidden objects return 404. |
| `transaction-failure` | Inject database failure inside commit using test-only hooks/fixtures. | No partial records/history/success event. |
| `max-supported.csv` | 500 structurally valid synthetic rows within 2 MiB. | Deterministic counts and completion within the selected host's measured supported request budget; otherwise reduce the advertised limit or add durable jobs. |

Implement test-only fault injection outside public API routes. Create fresh databases/scopes for fixtures whose expected totals would otherwise interact.

## Execution evidence

| Check / feature | Command or scenario | Result + count / timing | Revision | Evidence location |
|---|---|---|---|---|
| Not yet run | — | — | — | — |

Record passed, failed, skipped, and not-run outcomes separately. Never treat zero tests or only an open port as readiness.

## Blockers and decisions

| Item | Owner | Effect | Current state / next action |
|---|---|---|---|
| Official SIH requirements | HUMAN | May change scope or wording | Supply/confirm official statement. |
| Hosting/database projects and access | HUMAN | Blocks hosted validation, not local build | Select provider, approve costs, authorise access. |
| Core scope and metric review | SHARED | Proposed defaults can guide local work | Review P0 baseline. |
| Real APAAR interface | External authority | Blocks real-registry claims only | Mock is explicit core design. |
| Real-data legal/policy review | Authorised stakeholders | Blocks a real-data pilot only | Synthetic demo can proceed. |

## Completion record

Do not fill this section until checks exist:

- Delivered core features:
- Optional features actually delivered:
- Deployed services and verified revision:
- Checks passed / failed / not run:
- Known limitations:
- Demo operator and recovery instructions:
