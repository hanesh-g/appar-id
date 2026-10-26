---
type: Feature Specification
title: Feature specification
description: Specify each core and optional feature with rules, failures, and acceptance criteria.
tags: [apaar, features, acceptance, permissions]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-26T14:35:17Z"}
sources:
  - resource: 01-problem-and-scope.md
  - resource: 02-technical-design.md
---

# 03 — Feature specification

F01–F10 now have local implementations and checks. F11's hosted release gate remains incomplete. E0–E3 add explicit permissions, rule help/categories, resolution cases, and reviewed inline correction with local evidence. F12/F13, an LLM assistant, and LATER features are not implemented. The sections below define intended behaviour, not blanket completion: consult the [progress checklist](05-progress-checklist.md). Permission checks apply on the backend, including exports and guessed object IDs.

The [extension execution plan](11-feature-execution-plan.md) proposes additions to F09/F06 (resolution and correction preview), F14/F08 (provenance/help and illustrative categories), F13 (overlap review), F10 (audit integrity), and F12 (consent/QR). Those additions are planned, not delivered. Promote each contract here when its implementation starts; preserve the core acceptance rules below.

## F01 — Sign-in and institution isolation · CORE

**User value:** Staff can work on their own data without exposing another institution's students.

**Flow:** Open login → enter credentials → receive role and institution scope → open the permitted dashboard. Seed institution users for two different colleges and one officer. There is no public registration in core.

**Rules:** Use password hashes and short-lived signed tokens. Keep tokens in browser memory; a reload requires login. Institution scope comes from the authenticated account, never a trusted request parameter. Officers have explicit cross-institution read access. Officer write powers are not implied.

E0 enforcement: core-read and institution-write capabilities are explicit. Future/unknown roles, inactive accounts, an institution administrator without an institution, and an officer with an invalid institution binding receive no core access. Scope helpers enforce the same rule even when called outside an HTTP route. New roles must gain only their separately tested feature permissions.

**Failures:** Generic bad-credentials message; inactive account denial; expired token returns `401`; foreign institution resources return `404`; login throttling returns `429`.

**Acceptance:** Each role can sign in. Institution A cannot list, read, export, modify, commit, or discard B's data. Tests exercise real API requests rather than just hidden menu items.

## F02 — Programme and approved-intake setup · CORE

**User value:** Staff define the courses to which admissions belong and the limit shown in reports.

**Flow:** Programme list → select academic year → add/edit programme and intake → save → show audit entry.

**Inputs:** Name, year, non-negative approved intake. Institution comes from the account. An institution/name/year combination is unique. Do not allow moving a programme between institutions. Reject changing name/year once referenced by uploads or enrolments; use a new programme entry instead. An intake edit recomputes reports.

**Failures:** Negative intake, malformed year, duplicate programme, stale/foreign object, and unknown programme during upload produce clear errors. No silent auto-creation from CSV text.

**Acceptance:** A valid programme appears in upload selection. Invalid intake is refused. A committed programme's revised intake changes the dashboard and creates an audit event.

## F03 — CSV template and bounded upload · CORE

**User value:** An institution can submit many admissions through one supported format.

**Flow:** Select year → download template → prepare CSV → select file → upload → display dry-run result. Show the 500-row/2-MiB limits before upload.

**Rules:** Follow the header and types in the technical design. Require a request idempotency key. Escape dangerous spreadsheet formula values in downloaded CSV. Store staged personal data encrypted. Do not put uploaded rows in logs.

**Failures:** Empty file, wrong header, malformed UTF-8, excess rows/bytes, repeated keys, unknown programme, invalid date, and year mismatch. Do not accept Excel workbooks or claim XLSX support.

**Acceptance:** Supported files parse deterministically. Every row error includes its row number and field. Oversized input is rejected before unbounded memory use. A retry with the same request key does not create another batch.

## F04 — Simulated APAAR identity checks · CORE

**User value:** Staff can distinguish confirmed mock matches from missing or unresolved identity information.

**Flow:** Run local format checks → call the adapter for eligible rows → compare mock identity details → return a status and reason.

| Condition | Identity state | Row effect |
|---|---|---|
| Active mock ID; name and DOB match | `VERIFIED` | Identity passes. |
| No ID supplied | `MISSING` | Warning; structurally valid row can commit. |
| Bad format, not found, or inactive | `INVALID` | Warning; structurally valid row can commit unlinked. |
| ID exists, but name or DOB differs | `PENDING_CHECK` | Warning; do not link to that person. |
| Mock registry unavailable | `PENDING_CHECK` | Warning with `REGISTRY_UNAVAILABLE`; allow later retry. |

**Rules:** The 12-digit format is an assumption. Use strict fixture matching after documented normalisation; fuzzy similarity cannot verify identity. Only a successful identity match creates/links a person. Reassignment to a different verified person needs review.

**Failures:** Registry outage must not become “invalid ID.” A mismatch must not become verified because the ID exists. A retry that confirms identity must check person/programme uniqueness before linking; record any new conflict without silently merging.

**Acceptance:** The six-row identity fixture produces exactly the expected statuses. Missing/invalid identities remain visible and countable after commit. All views and reports identify the registry as simulated.

## F05 — Dry-run report and intake preview · CORE

**User value:** Staff see the result of a proposed change before it changes admissions.

**Screen:** Summary cards for submitted rows, acceptable rows, warnings, blocked rows, and identity gaps. Filterable row list. Issue groups with counts. Before/after active intake per programme. Clear commit options.

**Rules:** Issues have a stable code, field, severity, message, and next action. `ERROR` blocks a row; `WARNING` does not. A row can have multiple issues. Therefore issue totals may exceed affected-row totals. Define summary counts so they do not imply disjoint sets when they overlap.

Preview overlays acceptable upserts on current enrolments. Separately show held candidates with resolved keys and rows whose programme/key cannot be assigned. Never label raw submitted rows as unique enrolled students.

**Failures:** A stale report can change before commit. Commit must recheck it. A failed validation keeps the batch inspectable with safe error details and no partial main-record writes.

**Acceptance:** No main enrolments change before commit. A fixture produces known issue totals and a correct projected count. A correction to an existing record does not increase intake by one.

## F06 — Commit, correction upload, and duplicate prevention · CORE

**User value:** Staff can save useful data and correct it safely.

**Flow:** Review dry run → choose `commit_valid` or `all_or_nothing` → confirm → display saved/held counts. Correct a downloaded file externally and upload again.

**Rules:** `commit_valid` saves rows without blocking errors. `all_or_nothing` refuses any batch with blocking errors. Identity-only warnings do not block either mode. Commit the bounded batch atomically, with history and audit. Use canonical enrolment keys for upsert.

Unchanged correction rows are no-ops; changed rows increment version. A second commit returns the original result. An idempotency key reused with different content returns `409`. A new batch with the same students still cannot create duplicate enrolments.

**Failures:** Concurrent commits, new uniqueness conflicts, database failure, changed programme setup, and stale validation. Roll back failed commits. Preserve a useful failure result and an action to refresh/correct.

**Acceptance:** Double commit creates no new data or audit mutations. Corrected re-upload changes the intended fields once. A forced transaction failure leaves no partial committed records. Concurrent attempts respect uniqueness constraints.

## F07 — Enrolment lifecycle and record view · CORE

**User value:** Staff see current admissions and can record withdrawal, transfer, or completion.

**Flow:** Search within own institution by local student reference → open record → inspect identity/status/history → update allowed status and dates → save using expected version.

**Rules:** States are `ENROLLED`, `WITHDRAWN`, `TRANSFERRED`, `COMPLETED`. Non-active states require an end date. End date cannot precede start date. A return to active status requires clearing the end date and an audit entry. Identity correction goes through upload validation. Do not support moving a record to another institution by editing a field.

**Failures:** Invalid dates and stale versions are rejected. Concurrent edit returns `409`, not silent last-write-wins. Unknown or foreign record is not exposed.

**Acceptance:** A withdrawal decreases the active intake count while preserving history. A completed or transferred record remains visible under its status filter. Own-record changes cannot affect another institution's records.

## F08 — Officer and institution dashboards · CORE

**User value:** Users can see admission totals, intake concerns, and unfinished data-quality work.

**Screen:** Programme/year filters; active enrolments; approved intake; excess count; verified/missing/invalid/pending identities; held candidates; unassignable rows; last successful update. Officer can choose an institution. Institution scope is fixed.

**Rules:** Compute counts server-side from defined queries. Count all identity states among active enrolments. Do not count an earlier and corrected upload twice. Deduplicate assignable held candidates by canonical key across non-discarded batches; use the latest submitted candidate for each key, exclude candidates already superseded by a successful commit, and retain batch details for traceability. Unassignable rows are labelled raw-row totals, never unique admissions. Intake is a basic demo comparison, not an official quota-compliance ruling. Do not display names or DOB on aggregate charts.

**Failures:** Empty dataset shows an explanation, not fabricated sample metrics. API errors are visible. Loading is distinct from zero results. Zero approved seats must not cause division by zero.

**Acceptance:** The 65-admission fixture shows 65 active records, 5 missing identities, and 5 above an intake of 60. A re-upload does not change the total. The officer and institution see counts appropriate to their scope.

## F09 — Correction centre and retry · CORE

E2/E3 status: staff can open a case from a reported row, route its owner/state, and review its history. Held rows do not require an existing enrolment. A dedicated editor creates an exact encrypted preview before apply. Apply checks current case/record/intake/identity inputs and cannot overwrite newer changes. Successful repair supersedes source rows, preserves original input/issues/summary, and immediately removes current held work. Identity cases stay open until the remaining identity gap is resolved. Pending legacy previews must be uploaded again. Foreign cases/proposals, stale or expired proposals, altered payloads, false closure, and rollback/concurrent attempts are tested.

**User value:** Staff can turn error reports into a clear correction queue.

**Flow:** Open batch/issues → filter by issue code → read the correction instruction → download own-row correction CSV → edit and re-upload. For registry-unavailable identities, use a bounded “Retry identity checks” action after recovery.

**Rules:** Codes such as `PROGRAMME_UNKNOWN`, `DATE_INVALID`, `APAAR_MISSING`, `APAAR_INVALID`, `IDENTITY_MISMATCH`, and `REGISTRY_UNAVAILABLE` have consistent messages. Retry does not bypass matching or uniqueness checks. Missing IDs and identity mismatches are not automatically “fixed” by an outage retry.

Correction exports containing student data are available only to the owning institution, use explicit authentication, carry a sensitive-data notice, and use `Cache-Control: no-store`. No public object-storage URLs.

**Failures:** Registry still unavailable leaves state pending. Discarded batches do not appear as active correction work. Failed retry reports what remained unresolved.

**Acceptance:** A corrected row updates the existing enrolment. A recovery retry changes eligible pending identities and audits the update. CSV exports contain only scoped rows and safe spreadsheet cells.

## F10 — Change history and safe audit · CORE

**User value:** Users can explain when and why a record changed.

**Flow:** Open batch or enrolment → inspect chronological changes with actor, action, time, record ID, and non-sensitive differences.

**Rules:** Write a safe audit event in the same transaction as every state-changing operation. Record accepted uploads, commit, programme changes, lifecycle updates, and identity rechecks. Use batch-level upload/commit counts and per-record history where needed. Avoid unnecessary per-row event volume. Store no full APAAR, name, DOB, password, token, or raw CSV in audit metadata.

**Failures:** If audit persistence fails, the associated mutation fails. Core history is not described as immutable or tamper-proof. Reading history must enforce object scope.

**Acceptance:** A failed mutation leaves no misleading success event. A committed update has the actor and expected version history. Automated scans/tests verify representative audit/log output excludes known synthetic personal values and tokens.

## F11 — Repeatable synthetic demo and health checks · CORE

**User value:** The team can present and recover the demo predictably.

**Flow:** Run guarded migrations/seed → log into named demo roles → load fixture → follow demo script → reset only the designated demo database when authorised.

**Rules:** Seed is idempotent. No real student data. No published plaintext backend secrets. Demo account passwords use controlled delivery; public credentials require an isolated disposable dataset and explicit human approval. `/health` verifies API/database readiness without leaking configuration.

**Failures:** Restart must preserve records. Missing keys fail startup clearly without printing values. An unavailable database fails readiness. Seed/reset refuses a non-demo target.

**Acceptance:** Seed twice leaves stable counts. A deployed smoke journey passes. Nested frontend routes load directly. Backend restart preserves commits and can decrypt existing data with retained keys. A 500-row capacity result is recorded before advertising that limit.

## F12 — Student-approved verification and expiring QR link · NEXT

**User value:** A student can permit a verifier to check one record without sharing the full admission database.

**Flow:** Verifier signs in and requests a specified record for a stated purpose → the linked student sees the request → approves a field whitelist and expiry → verifier opens the permitted response or QR link → student can revoke access.

**Rules:** Add student and verifier roles with separately tested scope. Grant binds the student, record, verifier organisation, purpose, fields, and expiry. Use high-entropy opaque tokens stored as digests. Check current grant, signed-in verifier, expiry, revocation, and record scope on every request. QR encodes a link, not student data. Do not put the token or personal data in analytics or third-party scripts. Redact token-bearing paths in logs. Do not claim an official certificate.

**Failures:** Guessed token, wrong verifier, denied request, expired/revoked consent, inaccessible record, changed enrolment. Deny access with a generic response that does not reveal student existence.

**Acceptance:** Only the approved fields appear. Revocation and expiry deny the very next request. Another verifier cannot reuse the link. Student A cannot approve access to B's record. Browser/shared caches cannot retain the verification response.

**Cut line:** No student/verifier screens or public verification endpoint until the full permission path and negative tests pass.

## F13 — Possible overlapping-enrolment review · NEXT

**User value:** An officer can investigate conflicting records without falsely accusing a student.

**Flow:** After commit, compare date intervals for the same verified person → create an explainable review item → officer inspects minimal permitted evidence → marks reviewed with a reason.

**Rules:** Only verified identifier links establish the shared person. Names/DOB may suggest review but do not merge records. Use date intervals, not only current status, so a completed past record can still be checked for historical overlap. Record the policy assumption and exceptions. Institution users do not receive another college's private student details.

**Acceptance:** Non-overlapping transfer dates do not trigger an overlap. Overlapping dates trigger a review item, not automatic rejection. Repeated checks do not create repeated open items. Review resolution is audited.

## F14 — Source-linked rules/help assistant · NEXT

E1 status: deterministic demo-rule help is implemented, with pinned batch versions, source-code citations, applicability, and explicit missing official/human review dates. Historical snapshots and unsupported-version refusal are tested. No external LLM or reviewed official policy corpus is enabled.

**User value:** Staff can understand validation messages and find the right correction instructions.

**Smallest useful version:** Search the approved rules and glossary; show deterministic explanations with source links. An LLM is optional.

**If an LLM is added:** Retrieve only approved, current rule documents. Return cited answers and admit missing evidence. Use an approved provider and server-side credentials. Do not send student rows, names, DOB, tokens, or IDs. The assistant has no write tools, unrestricted SQL, or identity-decision powers. Apply timeouts and request limits. Treat retrieved content as data, not instructions.

**Acceptance:** Answers about missing IDs and intake use the selected rules and citations. Unsupported questions return a clear limitation. The core upload/commit flow still works when the LLM is unavailable. Privacy and prompt-injection tests pass before enabling it.

**Cut line:** A static help panel is the fallback. Do not invent answers to regulatory questions.

## F15 — Real integrations and large-volume ingestion · LATER

Features: approved APAAR adapter, institution API keys, ERP submission API, durable background jobs, rate-limit-aware retry, safe registry caching, resumable large batches, and monitoring.

Prerequisites: actual API contract and authorisation, verified provider limits, applicable identity matching policy, measured capacity, and durable queue design. API keys must be scoped, hashed, revocable, and audited.

Acceptance must include crash recovery, job idempotency, 50,000-row target measurements if claimed, and integration tests against an approved environment. The core's synchronous mock results do not satisfy these conditions.

## F16 — Production governance and operating controls · LATER

Features: legal/retention review, deletion workflows, key rotation, backups and restore drills, stronger audit integrity, managed identity/SSO, distributed rate limits, accessibility review, incident response, and policy versioning.

These require stakeholder and operator work as well as code. A working prototype does not establish compliance with the DPDP Act or approval by AICTE. Real student data remains blocked until the relevant requirements and permissions are resolved.
