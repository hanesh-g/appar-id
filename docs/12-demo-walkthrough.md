---
type: Operator Guide
title: Full local demo walkthrough
description: Update Windows safely and demonstrate correction, counts, overlap review, audit integrity, and consent.
tags: [apaar, windows, demo, consent, operations]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-27T16:50:46Z"}
sources:
  - resource: 05-progress-checklist.md
  - resource: 08-windows-setup.md
  - resource: 11-feature-execution-plan.md
---

# 12 — Full local demo walkthrough

This guide uses synthetic adult students and a simulated registry. The local features are implemented. Vercel/Render deployment and a Windows execution of these new commands remain unverified. See [executed evidence](05-progress-checklist.md).

## Update your Windows checkout

Stop the API with Ctrl+C before upgrading. Open PowerShell and run:

```powershell
Set-Location D:\Projects\appar-id\appar-id
git pull --ff-only
Set-Location backend
uv sync --frozen
uv run --frozen python ../scripts/configure_extensions.py --enable-audit --enable-consent
uv run --frozen alembic upgrade head
uv run --frozen python -m app.seed --demo
Set-Location ../frontend
npm.cmd ci
Set-Location ..
```

If Git reports local changes or a divergent branch, retain those changes and resolve the Git state before continuing. Do not reset the checkout to make the command pass.

The configuration helper adds separate audit/grant keys to your ignored `.env`. It preserves existing keys and passwords. Keep those keys across restarts. The seed adds missing demo users and preserves existing accounts, passwords, bindings, and records. New users receive the current local `DEMO_PASSWORD`; existing users retain their earlier password. Never paste `.env`, passwords, request codes, or shared tokens into an issue or chat.

Start the API and frontend in two PowerShell terminals:

```powershell
# Terminal 1
Set-Location D:\Projects\appar-id\appar-id
.\scripts\Start-Backend.ps1
```

```powershell
# Terminal 2
Set-Location D:\Projects\appar-id\appar-id
.\scripts\Start-Frontend.ps1
```

From a third terminal, `Invoke-RestMethod http://127.0.0.1:8000/api/v1/health` must report `status=ok`, `database=ok`, `registry=simulated`, `audit_chain_enabled=True`, and `consent_enabled=True`. Open the frontend address shown by Vite.

## Accounts and scope

| Account | What the user can do |
|---|---|
| `collegea@example.test` | Upload, review, commit, and correct the first college's records. |
| `collegeb@example.test` | Work with the second college's records. |
| `officer@example.test` | Read across colleges, review interval intersections, verify audit integrity. Cannot edit admissions or approve student consent. |
| `student1@example.test` | View verified records for synthetic student 001 and control consent. |
| `student2@example.test` | View only synthetic student 002's verified records and consent. |
| `verifier1@example.test` | Request consent and resolve grants addressed to this approved demo verifier. |
| `verifier2@example.test` | A different verifier for wrong-recipient demonstrations. |

The student accounts are pre-bound by the demo seed. There is no self-linking by entering an APAAR/DOB. Use separate browser profiles or sign out between roles. Reload requires sign-in because session tokens remain in memory.

## College: review and correct admissions

1. Sign in as College A. Open **Upload admissions** and select `fixtures/intake-65.csv` for `2026-27`.
2. Select **Validate and preview**. Read issues and the before/after intake. Nothing has entered the admission count yet.
3. Select **Commit batch** and confirm the reviewed operation. On an otherwise empty first-college dataset, Computer Science shows 65 active admissions, approved intake 60, and excess 5.
4. Open a rule explanation from an issue. It identifies the retained rule version and demo assumptions. Expand the category breakdown: base/supernumerary counts form one dimension; nationality flags can overlap.
5. Upload and commit `fixtures/structural-errors.csv`. It contains three held rows: two assignable candidates and one unassignable row. These are separate dashboard numbers.
6. Open the `DATE_INVALID` case for `STU-080`. In the Resolution Desk, select the next-action owner and case state if routing is needed. That assignment records responsibility; it does not send a notification or modify an upstream registry.
7. Select **Review a correction**. Change **Start date** to `2026-07-15`, select **Preview correction**, inspect the field comparison and intake effect, then select **Apply correction**.
8. The case resolves, one canonical admission is created, and Held Candidates falls from 2 to 1. The original report still contains its original error and input. The source row is marked `SUPERSEDED_BY_CORRECTION` for current work counts.

An expired proposal or changed case/record/intake needs a fresh preview. An old uncommitted CSV preview cannot overwrite a correction: re-upload and review it. Existing committed results remain repeatable. Exact counts above require the documented starting dataset; never delete shared data to reproduce a slide.

## Officer: review a date intersection

1. Sign in as College B. Upload and commit `fixtures/identity-cases.csv`. Its verified `STU-001` is the same synthetic person as College A's student 001.
2. College B's own record can show a generic pending-review notice. It does not identify the other college or disclose its record.
3. Sign in as the officer. The Admission oversight page highlights the review queue. Open **Overlap reviews → Review this overlap**, compare the two college records, choose a **Review outcome**, and select **Save review**. Outcomes are **Dual study reviewed**, **Transfer delay reviewed**, and **More evidence needed**. The filter starts at Needs review; select All reviews to inspect earlier decisions.
4. Both admission records remain. A date intersection is a review signal; it is not a fraud decision or proof of an official dual-study rule. Changed intervals can reopen or close the review with retained history.

For older synthetic records, initialise the queue once from `backend` with `uv run --frozen python -m app.reconcile_intervals --demo`. This explicit, repeatable backfill supports at most 500 people. It does not run on startup.

## Officer: verify the audit history

Open **Activity history → Run integrity check**. Expand **Check details and limits** for the watermark, legacy snapshot, and technical limits. A successful check reports its sequence watermark and any legacy snapshot captured when signing started. It detects retained-history changes under the documented threat model. It does not prove original legacy authenticity, survive complete database rollback undetectably, or protect against compromise of the application and its keys. There is no external anchor.

## Student and verifier: share only approved fields

1. Sign in as `student1@example.test`. Open **My records** and choose the intended college. **View student card** opens the personal record card before any sharing request. **Start sharing** opens a guided dialog and creates the one-use request code. With both college fixtures committed, this student has two legitimate records.
2. Select **Copy request code** and give that code to `verifier1@example.test` through your chosen channel. The code expires after 15 minutes and can create one matching request. It reveals no admission fields.
3. In the verifier workspace, open **Request access**, paste the code, choose a purpose, select fields such as **Programme** and **Institution**, and select **Send approval request**. The acknowledgement is generic. A guessed/expired/used code does not reveal whether a student exists.
4. Return to the student workspace and open **Requests**. Use **Refresh** or wait for its 15-second update. The pending list excludes expired requests. Inspect the verifier organisation, purpose, requested fields, linked record, and request expiry.
5. Check only **Programme**, choose an access duration of 5, 15, or 60 minutes, and select **Approve selected fields**. Nothing is preselected. Alternatively, select **Decline request**.
6. Approval moves to **Shared access** and brings the newly revealed QR/link into view. Review that sharing card: named verifier, purpose, approved fields, and expiry. Copy its link or share its QR with that verifier before leaving; the link is revealed once. The card is labelled as a synthetic demo and requires verifier sign-in. Its link carries an opaque token in its fragment; it contains no student record fields. There are no social-post buttons or permanent ID/certificate downloads.
7. The verifier opens the link and signs in, or opens **Verify a link** and pastes it into **Student consent link**. Select **Verify approved fields**. The result contains only Programme, although the original request asked for two fields. A QR by itself does not grant access to another verifier.
8. In the student workspace, open **Shared access → Stop sharing → Confirm stop sharing**. The displayed sharing card is hidden after that revoke succeeds, and the next request checked after revocation commits is refused. The **Access history** page records the verifier, purpose, field names, and time. Previously delivered information cannot be retracted.

The request expires after 24 hours. Grant expiry is at most 60 minutes and never later than the request. Resolve checks the live grant, caller/organisation, active student, expiry, revocation, and approved record version. Record changes invalidate the link. Approval also checks the record version shown to the student, so a concurrent correction requires review again.

If a link was lost, **Replace lost link** explicitly invalidates the previous grant and issues a new 15-minute link with the same fields, provided the record is unchanged and the request is still live. Only the latest grant can be replaced. A changed record needs a new request and consent. Keep links out of logs, analytics, and browser storage. Reloading after the fragment has been cleared can require opening the link again.

See [the interface guide and actual screenshots](13-demo-interface.md) for the visible student card and the role-specific navigation.

## Recovery and remaining human work

Retain the database, old rule packs, and all keys. Restart compatible code and verify health, an existing encrypted record, and audit integrity. To withdraw the student/verifier feature, set `CONSENT_ENABLED=false` in private settings and restart; the accounts and consent history remain stored and the new roles cannot sign in. Do not downgrade a populated schema or delete user bindings. Once the audit chain is active, keep signing enabled with its retained key; unsigned application writes are refused.

Vercel/Render account selection, costs, secure hosted secret entry, hosted migrations/restart checks, source/policy review, and presentation rehearsal remain human/shared release tasks. Deployment configuration is prepared in [the engineering guide](09-backend-engineering.md). Real registry access, minors/guardian consent, identity-proofing administration, real-data compliance, an LLM assistant, external audit anchoring, and key rotation are outside this delivered synthetic demo.
