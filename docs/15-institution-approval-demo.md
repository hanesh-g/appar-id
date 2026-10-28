---
type: Feature Specification
title: Institution approval review for the synthetic demo
description: A controlled officer review of synthetic institution and programme evidence, with admission-write gates.
tags: [apaar, institution, approval, demo, onboarding]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-28T03:41:29Z"}
sources:
  - resource: 01-problem-and-scope.md
  - resource: 09-backend-engineering.md
---

# 15 — Institution approval review

## Scope and claim

This feature demonstrates the missing institutional approval control. It uses a checked-in **synthetic catalogue**, never an AICTE API or a claim of official approval. Both colleges, their identifiers, campus descriptions, approval references, validity dates, and intake values are invented. Existing admissions/history remain readable. College accounts are still provisioned by an operator; public registration and representative identity proofing are outside this demo.

An officer reviews the institution, academic year, synthetic source, and matching programme/intake evidence before enabling admission submissions. An institution cannot approve itself. Unknown source entries, expired evidence, suspended approval, or programme/intake mismatches block new admission writes. A missing match means unverified, not an official finding of non-approval.

## Contract

- `GET /api/v1/institution-approvals?academic_year=2026-27`: own institution for college staff, both institutions for the officer; student/verifier roles denied. Returns effective status, evidence, matching programmes, current version, and recent decision history.
- `POST /api/v1/institution-approvals/{institution_id}/decisions`: officer-only, expected version and evidence digest, action `APPROVE_DEMO` or `SUSPEND`. Evidence comes exclusively from the server catalogue. The first decision expects version zero. Stale decisions fail with 409.
- Institution/year approvals retain their evidence snapshot, reviewer, time, version and decision events. Approval is explicitly `DEMO_FIXTURE`. Programme IDs, names, year, and intake are bound to that snapshot.
- Upload, commit, correction preview/apply and identity retry check the gate in domain services. Checks also run at commit/apply time, so a preview made before suspension cannot bypass a later decision. Lifecycle updates to existing admissions remain available to preserve accurate historical records.
- Programme creation/intake edits remain available to college staff, but new or changed programmes need matching evidence before admission writes. Such edits do not update approval evidence automatically.
- Writes and officer decisions acquire an institution-specific transaction advisory lock before programme/person/enrolment locks. Batch/proposal operation headers may precede it. Audit-chain locking remains last. The scope lock serialises suspension against admission writes.
- Migration creates additive tables only. Existing institutions start without approval; seed never silently approves them. Officers review the two existing colleges once after upgrade. Original records and keys are retained.

## Recording addition

Use the [action-by-action recording guide](14-demo-video-script.md), [full narration](demo-voiceover.txt), and [chapter audio text](demo-voiceover-sections.md). This version has 141 steps across 17 chapters, with no fixed runtime or overall character cap. Each step separates the spoken action from the result statement so the audience sees what the narration describes.

Chapter 02 shows College A's genuinely blocked upload. Chapter 03 shows the officer reviewing and approving **both demo colleges** separately. College A then refreshes its status and imports its file. **No college admission data is preloaded**: Chapter 09 introduces and imports College B's identity-cases file on screen, before the officer reviews the resulting overlap. This replaces the older preparation that loaded College B before filming.

Keep the source explicitly synthetic. The acknowledgement does not establish real AICTE approval or prove the identity of a college representative. For an exact first-approval demonstration use a separate fresh recording database; preserve earlier approvals/history in the existing database. If showing an already-approved college instead, describe its real history and avoid claiming a new first approval.

## Native Windows upgrade

Stop the backend before migrating. From the actual repository root:

```powershell
Set-Location D:\Projects\appar-id\appar-id
git pull --ff-only
Set-Location backend
uv run --frozen alembic upgrade head
Set-Location ..
.\scripts\Start-Backend.ps1
```

Restart the frontend in its other terminal with `scripts/Start-Frontend.ps1`. For an existing seeded dataset, no re-import, reset, new secret, or new account seed is needed. If setting up a new recording database, run the existing demo seed from `backend` before starting the API. It still leaves institution approval to the officer. Keep the database currently selected in your private `.env`.

Sign in as `officer@example.test`, open **Institution approval**, choose **2026-27**, and select **Review demo evidence** for the required college. Inspect the institution ID, campus, reference, dates, and programme/intake matches, check **I reviewed the synthetic evidence and matching programmes**, then select **Approve demo access**. Review both demo colleges before importing both colleges' fixtures. The college's own approval page is read-only.

**Suspend demo access** requires confirmation and blocks new uploads, pending commits, correction preview/apply and identity retry. It preserves existing admissions, histories and lifecycle updates. Re-approval requires current matching evidence. Changing an intake away from the catalogue value blocks that programme; approving other matching programmes cannot approve the changed value. A source change requires a fresh officer review. An approved row alone is insufficient when the requested programme/year/intake does not match its retained snapshot.

Campus and AICTE-like IDs are displayed from the invented source; no independent campus verification is claimed. The catalogue covers only the two demo colleges' Computer Science and Electronics programmes for 2026-27, intake 60, with illustrative validity 1 July 2026–30 June 2027. Other colleges/programmes/years remain unverified. A real deployment needs an authorised authoritative source, applicable programme/year approval rules, representative identity proofing, and operational re-verification; this demo does not establish any of them.

## Verification

Locally executed on 28 October 2026:

- All **128 backend tests passed**, 88.45 seconds, including 15 approval checks. They exercise pending/unknown/expired/source-changed denial, exact programme/intake/year binding, own-institution scope, officer-only decisions, student/verifier denial, caller-supplied evidence refusal, stale decision refusal, suspension versus staged commit/correction/retry, audit-failure rollback and concurrent writers.
- All **eight frontend tests passed**; lint, formatting, type checking and production build passed.
- All **seven browser journeys passed together**, 17.1 seconds. The new journey first gets an actual API refusal from an unreviewed college upload, then approves both colleges through the officer UI; existing admissions, correction, overlap, audit, consent and recovery journeys follow. Phone width 390 px has no page overflow; programme access states wrap into view. The existing shorter-height navigation/sign-out checks still pass.
- Fresh migration upgrade/downgrade passed. A populated c7 synthetic database was cloned to a separate target, then upgraded to c8: all **72 admissions and seven accounts** remained, and no institution was auto-approved. Alembic found no new model/schema operations.
- [Actual approval overview](assets/ux-institution-approval.png) and [evidence review dialog](assets/ux-institution-evidence-review.png) were captured from the running synthetic application and inspected. Browser signing/review is test activity, not a claim of human policy approval.

Normal development data was not reset, and no encryption/audit/grant key was regenerated. The browser download CDN was blocked, so browser verification used temporary Chromium from the npm registry; no application dependency was added. Native Windows, hosted and remote CI execution remain unverified. Official source verification, campus/representative identity proofing and human review remain outside this synthetic feature.
