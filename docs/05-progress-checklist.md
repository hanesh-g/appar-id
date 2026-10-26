---
type: Delivery Checklist
title: Progress checklist
description: Track implementation gates and executed evidence without invented completion.
tags: [apaar, progress, testing, release]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-26T14:35:17Z"}
sources:
  - resource: 03-feature-specification.md
  - resource: 04-implementation-phases.md
---

# 05 — Progress checklist

## Current state

Core code and E0–E3's correction workspace are locally verified. Latest backend regression: **68 passed**, 34.55 s. Frontend lint/format/types/build and **6 tests** passed; **2 browser journeys passed**, 7.6 s, including a held-row repair with immediate counter updates. A populated upgrade retained 65 enrolments and its existing case. Windows execution, hosted deployment, and remote CI remain unverified. E5–E7 are not delivered yet.

Use `[x]` only with current evidence. Use an evidence path, commit, test result, or deployed check in the final column. Record blocked work in the blocker table, rather than marking it done. CORE must pass before the demo is described as ready.

## Phase gates

| Gate | State | Evidence / decision |
|---|---|---|
| P0 — Core and contracts adopted | Proposed core implemented | Official statement/policy review remains human work. |
| P1 — Local and hosted skeleton | Local passed; hosting pending | Running API, PostgreSQL, frontend, nested route and readiness recovery. |
| P2 — Scoped users and data | Local checks passed | Isolation, encryption, seeded users, programme/audit tests. |
| P3 — Upload and dry run | Local checks passed | Identity fixture, file/row limits, filtering/export, no pre-commit writes. |
| P4 — Safe commit and correction | Local checks passed | Upsert, repeat/concurrent commit, rollback, stale conflict, recovery retry. |
| P5 — Reports and history | Local checks passed | 65/5/5 intake scenario, status/history, deduplicated candidates. |
| P6 — Deployed release gate | Local portion passed; hosting pending | Browser passed; no hosted account access/validation yet. |
| P7 — Selected extension iteration | E0–E3 local passed; later work pending | Rule help/categories, resolution cases, exact correction apply; see E0–E8 checklist. |

## P0 — Inputs and human decisions

- [ ] SHARED: Complete the official APAAR UI/adoption review; [research coverage and follow-up](10-apaar-platform-research.md) distinguish inspected peer sources from blocked official sources and untested hypotheses.
- [ ] HUMAN: Confirm official SIH statement and submission constraints.
- [ ] SHARED: Adopt core scope F01–F11; rank optional features.
- [ ] HUMAN: Confirm synthetic-only data and demo labels.
- [ ] SHARED: Confirm intake metric and warning/held-row policy.
- [ ] HUMAN: Select database provider and hosting plans/costs.
- [ ] HUMAN: Provide authorised account access and enter required values securely.
- [ ] SHARED: Adopt OKF document context; keep the reference agent out of the core runtime.

## P1 — Reproducible foundation

- [x] AI: Python/Node pins and compatible locked dependencies.
- [x] AI: Environment-name template contains no secrets.
- [x] AI: PostgreSQL, migration command, API, and frontend start locally.
- [x] AI: Database-ready health check succeeds and fails correctly.
- [ ] AI: Early hosted frontend reaches hosted backend/database.
- [x] AI: Nested frontend URL loads directly.
- [x] AI: Actual setup/start/check commands recorded.

## P2 — Access and data safety · F01/F02

- [x] AI: Migrations succeed against a fresh PostgreSQL database.
- [x] AI: Idempotent seed creates two institution users and an officer.
- [x] AI: Valid login works; bad/expired/inactive credentials fail.
- [x] AI: Passwords hashed; tokens constrained; secret fields excluded from responses.
- [x] AI: Foreign institution list/detail/edit/export/batch access fails.
- [x] AI: Programme validation, uniqueness, intake edit, and audit work.
- [x] AI: Sensitive fields encrypt/decrypt; ciphertext tampering is rejected.
- [ ] HUMAN: Role views and demo credential distribution reviewed.

## P3 — Upload and review · F03/F04/F05

- [x] AI: Template matches the documented CSV contract.
- [x] AI: File/row limits are enforced during bounded parsing.
- [x] AI: Empty, malformed, wrong-header, duplicate-key, unknown-programme, and bad-date cases fail clearly.
- [x] AI: Request idempotency returns the original batch; changed content conflicts.
- [x] AI: Known identity fixture produces exact expected states and reasons.
- [x] AI: Missing/invalid identity is a warning, not a structural block.
- [x] AI: Outage results are pending, not invalid.
- [x] AI: Dry run writes no main enrolments.
- [x] AI: Issue counts, fields, next actions, and intake preview are correct.
- [x] AI: Authenticated CSV export is scoped, non-cacheable, and formula-safe.
- [ ] HUMAN: Correction instructions and mock labels make sense to a user.

## P4 — Save and correct · F06/F09

- [x] AI: `commit_valid` saves acceptable rows and holds errors.
- [x] AI: `all_or_nothing` refuses structural errors; identity-only warnings remain allowed.
- [x] AI: Commit writes records/history/audit/result atomically.
- [x] AI: Repeat commit causes no mutation.
- [x] AI: Same students in a new batch do not duplicate enrolments.
- [x] AI: Changed correction updates once; unchanged rows are no-ops.
- [x] AI: Stale preview/new conflicts produce a clear refusal or refreshed result.
- [x] AI: Concurrent attempts respect locks/constraints.
- [x] AI: Forced mid-transaction failure rolls back all associated changes.
- [x] AI: Recovery retry updates only eligible outage-pending rows and audits changes.
- [x] AI: Identity reassignment/uniqueness conflict cannot silently merge people.
- [ ] HUMAN: End-to-end correction flow reviewed.

## P5 — Results and accountability · F07/F08/F10

- [x] AI: Record list/detail and history are scoped and paginated.
- [x] AI: Lifecycle dates validate; stale edit returns `409`.
- [x] AI: Withdrawal changes active intake and preserves history.
- [x] AI: 65-admission fixture produces 65 active, 5 missing, 5 excess.
- [x] AI: Repeated batches/corrections do not inflate dashboard totals.
- [x] AI: Held candidates are deduplicated; unassignable raw rows are labelled separately.
- [x] AI: Empty/loading/error states are real, not seeded visual placeholders.
- [x] AI: Audit writes are transactional and contain no personal values/tokens.
- [ ] HUMAN: Report language avoids unsupported official-compliance claims.

## P6 — Release gate · F11

- [x] AI: Backend rule/API/integration suite passed with nonzero test counts.
- [x] AI: Frontend typecheck/lint/relevant tests/build passed.
- [x] AI: Browser core smoke passed against real API responses.
- [x] AI: Clean-database migration and double-seed passed.
- [x] AI: Frozen-lockfile installation reproduced.
- [ ] AI: Advertised maximum file tested on the actual hosting plan; timing recorded.
- [ ] AI: Hosted login/upload/commit/correction/dashboard/denial checks passed.
- [ ] AI: Exact CORS origins, HTTPS, database TLS, and frontend API URL checked.
- [x] AI: API restart preserves records and decryption capability.
- [x] AI: No dependency on ephemeral uploaded files or in-memory jobs.
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

## Planned extension iteration — E0–E8

The [execution plan](11-feature-execution-plan.md) maps the supplied five task-card groups to dependency phases. E0–E3 are implemented and checked locally. Later phases remain incomplete unless checked below. The supplied policy/adoption claims still require dated primary sources.

- [x] E0 / AI: Replace implicit no-institution global scope with explicit role permissions; exercise current routes and unknown-role denial. Evidence: eight route/scope tests passed; full backend suite **45 passed** in 23.87 s.
- [ ] E0 / SHARED: Confirm synthetic scope, Release A cut, and human hosting/source-review queue.
- [x] E1 / AI: Retained rule packs, actual-code coverage, historical batch references, deterministic help API/UI, and executable-version checks. Evidence: source coverage, snapshot retention/tamper checks, and populated Alembic upgrade tests.
- [x] E1 / AI: Scoped base/supernumerary counts and independent NRI/OCI/foreign dimensions with overlapping-flag tests. Evidence: mixed-category PostgreSQL test and browser expand/collapse view.
- [x] E2 / AI: Staged-row/enrolment resolution cases, deduplicated origins, guarded transitions, safe event history, scoped API/UI. Evidence: five case tests plus browser routing.
- [x] E3 / AI: Encrypted exact correction proposals, masked field differences, versions, expiry, and intake preview. Evidence: proposal/field/scope/integrity/expiry tests and browser comparison.
- [x] E3 / AI: Atomic apply, idempotency, stale-batch protection, case closure checks, and rollback/concurrency tests. Evidence: 13 correction tests; repaired rows leave held work without changing historical reports; concurrent promotions share one person.
- [ ] E4 / SHARED: Release A local regression/browser/migration checks passed; hosted validation, hosted restart, and human rehearsal remain pending.
- [ ] E5 / AI: Verified-person interval reconciliation, concurrent detection, review lifecycle, limited officer writes, and privacy-safe institution notices.
- [ ] E6 / AI: Separate audit key, dedicated chain head, honest legacy baseline, snapshot verifier, and tamper/concurrency/rollback tests.
- [ ] E7a / AI: Student/verifier profiles and explicit route scope, adult synthetic accounts, private expiring request handles, and repeatable seed.
- [ ] E7b / AI: Requests, field-limited grants, purpose/expiry/record binding, separate token key, denial/revoke/reissue, and access audit.
- [ ] E7c / AI: Student/verifier browser flow, token-safe QR delivery, no-store responses, and full wrong-user/expired/revoked/stale-record tests.
- [ ] E8 / SHARED: Release B upgrade/deployment/restart and full hosted demonstration pass; preserved keys and known limits documented.
- [ ] HUMAN: Review applicable policy sources, correction ownership, student linking/verifier approval, and real-data requirements before any official claim or real-data pilot.

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
| E2/E3 local Release A | Full backend; frontend checks/build; real-browser routing/repair; populated upgrade | **68 backend passed**, 34.55 s; **6 frontend passed**; **2 browser passed**, 7.6 s; retained **65 enrolments / 1 case** on upgrade | Correction workspace implementation | `test_resolution_cases.py`, `test_corrections.py`, shared regression; fresh isolated release database. Initial tests exposed snapshot overwrite and implicit selector-label ambiguity, both fixed before passing. |
| E1 rules/categories | Backend regression; frontend checks/build; expanded browser journey | **50 backend passed**, 27.62 s; **6 frontend passed**; **1 browser passed**, 4.3 s | E1 implementation | Rule/catalog/category tests; populated migration; `frontend/tests/core.spec.ts`. First browser attempt found an ambiguous assertion matching new helper text; exact-label assertion corrected and rerun passed. |
| E0 explicit permissions | Focused permission matrix, then `uv run --frozen pytest -q` | **8 focused passed**; **45 full-suite passed**, 23.87 s | E0 implementation | `backend/tests/test_extension_permissions.py`; future/unknown and invalid-scope principals denied on 18 protected route/method combinations, officer read-only preserved |
| Backend | `uv run --frozen pytest -q` | **32 passed**, final run 17.25 s | Working tree before release commit | `backend/tests/` |
| Backend style | `ruff check` and `ruff format --check` | Passed | Same | `backend/pyproject.toml` |
| Frontend | lint, format, Vitest, TypeScript + Vite build | **6 tests passed**; all checks/build passed | Same | `frontend/src/*.test.*` |
| Browser | `npm run smoke` against local API/UI | **1 passed**, final run 5.2 s | Same | `frontend/tests/core.spec.ts` |
| Capacity, local only | Actual HTTP upload of `max-supported.csv` | **500 rows**, 0 blocking errors, **0.107 s** dry run | Same | HTTP request, local development machine; not a hosted benchmark |
| Readiness/recovery | Stop/restart only project database; check API and records | **503 during outage**, 200 after recovery; 65 admissions and decryption preserved | Same | Functional local checks |
| Routing | Direct HTTP request to frontend nested `/records` | 200 and application HTML | Same | Local Vite; hosted SPA rewrite unverified |
| Dependencies | `uv sync --frozen`; `npm ci --offline` from cache | Frozen installs reproduced | Same | Committed lockfiles |
| Windows / hosting / CI | Native Windows, Render, Vercel, GitHub Actions | **Not run** in those environments | — | Follow Windows/engineering guides |
| Local origin follow-up | `uv run --frozen pytest -q tests/test_local_cors.py` | **5 passed**; localhost/IPv4 preflights accepted locally, unexpected origins/ports denied, hosted aliases denied | Follow-up fix | `backend/tests/test_local_cors.py`; user also confirmed API/database health on Windows |

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

- Delivered core features: F01–F10 locally; local parts of F11.
- Optional features actually delivered: none.
- Deployed services and verified revision: none; local running services only.
- Checks passed / failed / not run: see execution evidence; a sandbox-denied attempt was diagnosed and rerun with required permissions.
- Known limitations: simulated registry; 500-row/2-MiB limit; no consent/LLM integration; single-process login throttle; Windows and hosted runtime unverified.
- Demo operator and recovery instructions: docs/08-windows-setup.md. No destructive reset helper is provided; use an explicitly disposable fresh database.
