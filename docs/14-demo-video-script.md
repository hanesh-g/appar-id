---
type: Demo Recording Script
title: Action-by-action narration and recording guide
description: A complete walkthrough with explicit role transitions and before-action, action, wait and result narration for each recording step.
tags: [apaar, demo, recording, voiceover, sih, walkthrough]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-28T05:48:21Z"}
sources:
  - resource: 12-demo-walkthrough.md
  - resource: 13-demo-interface.md
  - resource: 15-institution-approval-demo.md
  - resource: 05-progress-checklist.md
---

# 14 — Detailed demo: follow every action with its narration

**Use this document while recording.** The current request is for a complete walkthrough without a time limit. This version replaces the earlier short narration, fixed timestamps and total character cap. The introduction stays brief; the explanation grows as each action occurs.

There are **141 numbered steps across 17 chapters**. Every step includes **Say before → Do → Wait for → Say after**, with the final part included only when a result needs explaining. The [full narration-only text](demo-voiceover.txt) has one paragraph per numbered step: 2,211 words and 14,153 characters. The [chapter-by-chapter narration](demo-voiceover-sections.md) is arranged for separate audio clips. Each chapter's spoken text is below 5,000 characters; that is a convenience for voice tools, not a limit on this walkthrough.

Speak the before-action line, perform the named action, wait until the named screen/result is visible, and only then speak the after-result line. If the interface shows something else, pause the recording and use the recovery table. Do not read a future result while a request is loading.

## The story the audience will follow

Deccan Institute's administrator starts with an unreviewed institution. The officer checks synthetic institution and programme evidence and enables both demo colleges. Deccan imports admissions, separates identity warnings from structural errors, and repairs one blocked candidate. Riverdale then imports its own records **on screen**, creating the context for a cross-college overlap review. The officer reviews that overlap and the audit history. Finally, the shared student chooses a single Deccan record, approves only Programme for a named verifier, and revokes the resulting access.

No college admission file is preloaded for this version. Approval, all three imports, correction, the second-college overlap, consent and revocation happen in the visible sequence. This makes each later screen follow from an earlier action the audience saw.

## Record in chapters

Use this opening title overlay: **APAAR Workspace · SIH 2026 · AICTE · SIH26263**. Display the full problem title below it: **Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions**. The short spoken introduction identifies the statement by its code.

Record screen and microphone together, one chapter at a time. This naturally aligns the spoken action with the visible action. Pause between chapters, and cut the pause in the editor. Keep the step numbers on a second screen or phone; they are operator cues and are not spoken.

If using a separate voice track, record one chapter's footage, then record that chapter's exact narration while watching its footage. Align the after-result sentence to the loaded result, and hold that result while speaking. The existing short voice-over does not contain these additional lines; retain it as a backup and record the expanded chapters. Do not force this script back into the earlier seven-minute edit.

Read only the quoted SAY text. Do not read the step number, action instructions, wait conditions, filenames in code formatting, or setup notes unless the spoken text explicitly includes them. Copy the entire chapter's spoken block from the [chapter narration file](demo-voiceover-sections.md) if a voice tool needs an audio chunk.

## Prepare outside the recording

### 1. Update the project and keep credentials private

Stop both servers. In PowerShell:

```powershell
Set-Location D:\Projects\appar-id\appar-id
git pull --ff-only
Set-Location backend
uv run --frozen python ../scripts/configure_extensions.py --enable-audit --enable-consent
```

The helper is run from **backend** and preserves existing keys/passwords. Keep `MOCK_REGISTRY_OUTAGE=false` in the private root `.env`. The programme/year demo evidence must still be applicable on the recording date. This is synthetic evidence; no real AICTE or APAAR connection is used.

### 2. Use a separate fresh recording database

The exact narration below expects both colleges to start with **zero admissions, no approval decisions, no cases and no consent requests**. The seed may create synthetic people and accounts; those are not admissions. Preserve your existing imported database.

Create the recording database **before** changing the application's connection setting. From PowerShell, use your installed PostgreSQL 18 tools:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "CREATE DATABASE apaar_recording_walkthrough OWNER apaar_app;"
```

Enter the PostgreSQL administrator password locally. Continue after `CREATE DATABASE` is reported. If that name exists, choose another new name, such as `apaar_recording_walkthrough_02`; do not drop or empty the existing database. In TablePlus, the equivalent SQL can be run from the `postgres` administrator connection, with database `postgres` selected.

In the root `.env`, change **only the database name within `DATABASE_URL`** to the newly created target. Keep every password, key, host, port and connection option; leave `TEST_DATABASE_URL` unchanged. A missing-database error means this creation step or the database name needs checking; Alembic creates tables, not the database itself.

Then initialise the selected target:

```powershell
Set-Location D:\Projects\appar-id\appar-id\backend
uv run --frozen alembic upgrade head
uv run --frozen python -m app.seed --demo
```

The ordinary seed creates missing demo accounts/programmes and preserves existing data. It never grants institution approval or imports admissions. For this newly created database, accounts use the private `DEMO_PASSWORD`. Do not import any CSV or approve either college during preparation.

### 3. Start and check the application

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

```powershell
# Terminal 3
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expect API/database `ok`, registry `simulated`, and both audit and consent enabled. Log in successfully before recording. Do not show terminals, `.env` or passwords in the video.

Use local recording if it is reliable. Hosting is optional. A hosted recording needs the reachable hosted Python API and PostgreSQL, correct frontend API address, HTTPS and exact allowed frontend origin. Verify the journey on that deployment; the spoken script makes no deployment claim.

### 4. Open five authenticated tabs in this exact order

| Tab | Account | Role shown to the audience | Starting page |
|---|---|---|---|
| Ctrl+1 | `collegea@example.test` | Deccan Institute administrator / College A | Overview, zero admissions, approval needed |
| Ctrl+2 | `officer@example.test` | Officer | Overview |
| Ctrl+3 | `collegeb@example.test` | Riverdale administrator / College B | Overview, zero admissions, approval needed |
| Ctrl+4 | `student1@example.test` | Synthetic student one | Overview, no submitted records yet |
| Ctrl+5 | `verifier1@example.test` | Demo admissions verifier | Overview |

Sign in before recording so passwords are not captured. Sessions stay in each tab's memory and expire after one hour. Use in-app refresh buttons. A browser reload needs sign-in again; it does not erase database records. If a session expires, pause the clip, sign in privately and resume at a chapter boundary.

Have the three CSVs easy to select from `D:\Projects\appar-id\appar-id\fixtures`: `intake-65.csv`, `structural-errors.csv`, and `identity-cases.csv`. Download/file-picker locations depend on your Windows setup; the step names below specify the exact files.

### 5. Check the starting state and expected progression

| Point in the story | Expected state on this fresh dataset |
|---|---|
| Before recording | Both colleges: 0 admissions and Officer review needed. No case or consent history. |
| After officer review | Both colleges: Demo approval active. Computer Science and Electronics each match source intake 60 for 2026-27. |
| After Deccan's intake-65 commit | Deccan: 65 active admissions, 60 simulated matches, 5 identity gaps, 5 above basic intake. |
| After structural-errors is committed | No new admissions; 3 held rows comprise 2 held candidates and 1 unassignable row. |
| After STU-080 is corrected | Deccan: 66 active admissions; 1 held candidate and 1 unassignable row remain. The original report still has its original 3 blocking errors. |
| After Riverdale's identity-cases commit | Riverdale: 6 active admissions. Officer: 2 colleges, 72 active enrolments, 1 open overlap. |
| Student after both imports | Student one can see 2 linked records, one for each college. Choose Deccan's record for sharing. |
| Consent example | Verifier requests Programme + Institution; student approves Programme only for **15 minutes**. |
| After revocation | The same grant link is refused on a new check; the prior successful access remains in history. |

If your numbers differ, stop before recording a claim. An existing import, earlier correction, wrong college, incorrect year, edited fixture or outage setting can change the outcome. Start another separate recording database rather than resetting history. Do not rehearse the irreversible approval/commit/apply steps on your only recording dataset.

## Recording script

Each chapter can be a separate clip named with its chapter number. Start the next chapter on the stated role/page. Every role change is announced in the narration; every result line is spoken after the result appears.

| Chapter / clip | Steps | Role | Audience task |
|---|---|---|---|
| 01 | 001–003 | College A · tab 1 | Introduce the workspace and the college's starting position |
| 02 | 004–009 | College A · tab 1 | Show why an unreviewed college cannot upload |
| 03 | 010–022 | Officer · tab 2 | Review and approve both synthetic institutions |
| 04 | 023–035 | College A · tab 1 | Return to College A and validate its admission file |
| 05 | 036–043 | College A · tab 1 | Commit College A's acceptable rows and explain the dashboard |
| 06 | 044–056 | College A · tab 1 | Stage a file with structural errors |
| 07 | 057–064 | College A · tab 1 | Preview, apply and verify the correction |
| 08 | 065–071 | College A · tab 1 | Show the retained report and the saved enrolment |
| 09 | 072–082 | College B · tab 3 | Import the second college's records on screen |
| 10 | 083–092 | Officer · tab 2 | Review the overlap as an officer |
| 11 | 093–097 | Officer · tab 2 | Inspect activity and check its integrity |
| 12 | 098–106 | Student · tab 4 | Open the student's records and personal card |
| 13 | 107–114 | Verifier · tab 5 | Submit a specific request as the verifier |
| 14 | 115–123 | Student · tab 4 | Approve fewer fields as the student |
| 15 | 124–128 | Verifier · tab 5 | Open only the approved field as the verifier |
| 16 | 129–139 | Student → Verifier → Student | Stop sharing and prove the same link is refused |
| 17 | 140–141 | Student · tab 4 | Close the story |

## Chapter 01 — Introduce the workspace and the college's starting position

**Role:** College A · tab 1. **Purpose:** Establish the SIH context and show that this college starts with no admissions.

### Step 001

**SAY BEFORE:**

> This is APAAR Workspace, our prototype for Smart India Hackathon 2026, AICTE problem statement SIH26263. Missing IDs and incorrect records complicate admissions. We help colleges check and correct data, while students control record sharing. Let's see it in action using synthetic data and simulated checks.

**DO:** Keep College A's Overview visible. Add the SIH title as a brief overlay in the editor; do not open an extra browser tab.

**WAIT FOR:** The College A overview and demo label are visible.

### Step 002

**SAY BEFORE:**

> I am starting as the administrator of Deccan Institute of Technology, our first demo college.

**DO:** Point to the institution account in the sidebar, then the Active admissions card.

**WAIT FOR:** Active admissions shows 0 on the fresh dataset.

**SAY AFTER THE RESULT:**

> This college has no saved admissions yet.

### Step 003

**SAY BEFORE:**

> The college also needs an officer's approval before it can submit admissions.

**DO:** Point to the approval notice above the dashboard.

**WAIT FOR:** The notice reads Officer review needed.

**SAY AFTER THE RESULT:**

> I will first show how that requirement is enforced.

## Chapter 02 — Show why an unreviewed college cannot upload

**Role:** College A · tab 1. **Purpose:** Demonstrate an actual blocked request before any admission is saved.

### Step 004

**SAY BEFORE:**

> I open Upload admissions to begin the college's submission.

**DO:** Click Upload admissions in the sidebar.

**WAIT FOR:** The Upload admissions page and approval notice are loaded.

### Step 005

**SAY BEFORE:**

> I select the academic year twenty twenty-six to twenty-seven.

**DO:** Open Academic year and choose 2026-27.

**WAIT FOR:** Academic year shows 2026-27.

### Step 006

**SAY BEFORE:**

> I choose our prepared intake sixty-five CSV file from the fixtures folder.

**DO:** Click the Student CSV file control. In the file picker open the fixtures folder and select intake-65.csv.

**WAIT FOR:** The upload area shows intake-65.csv.

**SAY AFTER THE RESULT:**

> This file contains synthetic admissions only.

### Step 007

**SAY BEFORE:**

> I try to validate this file while the college is still waiting for approval.

**DO:** Click Validate and preview.

**WAIT FOR:** The page shows an approval-required error, not a batch review.

**SAY AFTER THE RESULT:**

> The request is blocked. No admissions have been saved.

### Step 008

**SAY BEFORE:**

> I open View approval to see what is missing.

**DO:** Click View approval in the approval notice.

**WAIT FOR:** The Institution approval page shows only Deccan Institute of Technology.

### Step 009

**SAY BEFORE:**

> The institution and programme evidence still need review.

**DO:** Point to Officer review needed and the read-only programme rows.

**WAIT FOR:** The programme rows say Awaiting officer review and there is no college-side approval button.

**SAY AFTER THE RESULT:**

> College staff cannot approve their own institution. I will switch to the officer account for that decision.

## Chapter 03 — Review and approve both synthetic institutions

**Role:** Officer · tab 2. **Purpose:** Show the evidence, explicit approval, and recorded decision before either college imports data.

### Step 010

**SAY BEFORE:**

> I am now using the officer workspace, which can review institutions across both colleges.

**DO:** Switch to the pre-signed-in Officer tab with Ctrl+2.

**WAIT FOR:** The officer account and Admission oversight page are visible.

### Step 011

**SAY BEFORE:**

> I open Institution approval to review the colleges' evidence.

**DO:** Click Institution approval in the sidebar.

**WAIT FOR:** Two institution cards are loaded.

### Step 012

**SAY BEFORE:**

> I select the same academic year as the college's submission.

**DO:** Open Academic year and choose 2026-27.

**WAIT FOR:** Both cards apply to 2026-27.

### Step 013

**SAY BEFORE:**

> For Deccan Institute, I check the synthetic institution identifier, campus, approval reference, validity dates, and programme intakes.

**DO:** Point to Deccan Institute of Technology's evidence facts and programme rows.

**WAIT FOR:** The Deccan card shows invented demo identifiers, two matching programme intakes of 60, and Officer review needed.

**SAY AFTER THE RESULT:**

> These are simulated catalogue entries, not actual AICTE approval records.

### Step 014

**SAY BEFORE:**

> I open Review demo evidence for this institution.

**DO:** Click Review demo evidence inside the Deccan Institute card.

**WAIT FOR:** The Review synthetic approval evidence dialog is open.

### Step 015

**SAY BEFORE:**

> The dialog identifies the institution, year, source, and programmes that this decision will enable.

**DO:** Point to the dialog's institution, year, programme list and synthetic-source statement.

**WAIT FOR:** The dialog lists Computer Science and Electronics, each with intake 60.

**SAY AFTER THE RESULT:**

> Approval applies to this evidence and these programmes.

### Step 016

**SAY BEFORE:**

> I acknowledge that I have reviewed the displayed synthetic evidence.

**DO:** Check I reviewed the synthetic evidence and matching programmes.

**WAIT FOR:** The acknowledgement is checked and Approve demo access is enabled.

### Step 017

**SAY BEFORE:**

> I approve demo access for Deccan Institute.

**DO:** Click Approve demo access.

**WAIT FOR:** The dialog closes and the Deccan card shows Demo approval active.

**SAY AFTER THE RESULT:**

> Its matching programmes can now accept admission submissions.

### Step 018

**SAY BEFORE:**

> I expand Evidence and decision history to check the recorded decision.

**DO:** Open Evidence and decision history in the Deccan card.

**WAIT FOR:** The retained evidence reference, reviewer, decision time and version are visible.

**SAY AFTER THE RESULT:**

> The approval decision is recorded with its evidence.

### Step 019

**SAY BEFORE:**

> I will also enable Riverdale Technical College, our second demo college, for a later cross-college example.

**DO:** Scroll to Riverdale Technical College's card.

**WAIT FOR:** Riverdale still shows Officer review needed.

**SAY AFTER THE RESULT:**

> No admission data has been imported for Riverdale yet.

### Step 020

**SAY BEFORE:**

> I open Riverdale's evidence review and check its institution, academic year, validity and programme list.

**DO:** Click Review demo evidence inside the Riverdale card.

**WAIT FOR:** The Riverdale review dialog is loaded with matching synthetic evidence.

### Step 021

**SAY BEFORE:**

> I acknowledge the Riverdale evidence separately.

**DO:** Check I reviewed the synthetic evidence and matching programmes.

**WAIT FOR:** The Riverdale acknowledgement is checked.

### Step 022

**SAY BEFORE:**

> I approve demo access for Riverdale.

**DO:** Click Approve demo access.

**WAIT FOR:** The Riverdale card shows Demo approval active.

**SAY AFTER THE RESULT:**

> Both colleges are now enabled, but their admissions remain separate.

## Chapter 04 — Return to College A and validate its admission file

**Role:** College A · tab 1. **Purpose:** Move from institution approval to programme setup and an explained dry run.

### Step 023

**SAY BEFORE:**

> I return to the Deccan Institute administrator to continue the blocked submission.

**DO:** Switch to College A with Ctrl+1.

**WAIT FOR:** The College A Institution approval page is visible.

### Step 024

**SAY BEFORE:**

> I refresh the college's approval status.

**DO:** Click Refresh approvals.

**WAIT FOR:** The card shows Demo approval active and both programme rows show Enabled in demo.

**SAY AFTER THE RESULT:**

> The college can now submit records for these matching programmes.

### Step 025

**SAY BEFORE:**

> Before uploading, I open Programmes to check the configured courses and intake.

**DO:** Click Programmes in the sidebar.

**WAIT FOR:** The Programmes & intake table is loaded.

### Step 026

**SAY BEFORE:**

> Computer Science is configured for this year with an intake of sixty.

**DO:** Point to the Computer Science row for 2026-27.

**WAIT FOR:** The Computer Science row shows 2026-27 and 60.

**SAY AFTER THE RESULT:**

> That is the demo comparison limit used in the report.

### Step 027

**SAY BEFORE:**

> I return to Upload admissions.

**DO:** Click Upload admissions in the sidebar.

**WAIT FOR:** The upload form is loaded and the approval notice is active.

### Step 028

**SAY BEFORE:**

> I keep the upload in the same academic year.

**DO:** Open Academic year and choose 2026-27.

**WAIT FOR:** Academic year shows 2026-27.

### Step 029

**SAY BEFORE:**

> I select the intake sixty-five CSV again for the actual validation.

**DO:** Click the Student CSV file control and select fixtures/intake-65.csv.

**WAIT FOR:** The selected filename is intake-65.csv.

### Step 030

**SAY BEFORE:**

> I select Validate and preview to check the file without committing admissions.

**DO:** Click Validate and preview.

**WAIT FOR:** The intake-65.csv batch review loads.

### Step 031

**SAY BEFORE:**

> The report contains sixty-five rows: sixty without issues, five warnings, and zero blocking errors.

**DO:** Point to the four report summary cards.

**WAIT FOR:** The cards show 65, 60, 5 and 0 respectively.

**SAY AFTER THE RESULT:**

> These are the results for this uploaded file.

### Step 032

**SAY BEFORE:**

> I filter the report to the missing APAAR identifiers.

**DO:** Click the APAAR missing issue filter.

**WAIT FOR:** Five warning rows are displayed.

**SAY AFTER THE RESULT:**

> These rows have identity gaps, but they are not structurally blocked admissions.

### Step 033

**SAY BEFORE:**

> I open Why this issue to understand the warning and the next action.

**DO:** Click Why this issue? on the first missing-ID row.

**WAIT FOR:** The Why this issue needs attention dialog has loaded its explanation.

**SAY AFTER THE RESULT:**

> The guidance explains what staff should review. Its source is a synthetic demo rule.

### Step 034

**SAY BEFORE:**

> I close the explanation and return to the file review.

**DO:** Close the rule-help dialog using its top-right X, labelled Close dialog.

**WAIT FOR:** The report is visible again.

### Step 035

**SAY BEFORE:**

> I scroll to the intake preview before saving anything.

**DO:** Scroll to Intake preview at review time.

**WAIT FOR:** Computer Science shows Before 0, After 65, Limit 60, and Excess 5.

**SAY AFTER THE RESULT:**

> The preview shows the proposed effect. These admissions have not been committed yet.

## Chapter 05 — Commit College A's acceptable rows and explain the dashboard

**Role:** College A · tab 1. **Purpose:** Show the explicit save and distinguish admissions, identity gaps and held work.

### Step 036

**SAY BEFORE:**

> I choose Save acceptable rows and hold errors, so structural problems stay outside the saved admissions.

**DO:** Scroll to Ready to save and choose Save acceptable rows; hold errors under Commit mode.

**WAIT FOR:** The chosen commit mode is visible.

### Step 037

**SAY BEFORE:**

> I select Commit batch to save the reviewed submission.

**DO:** Click Commit batch.

**WAIT FOR:** The browser asks for confirmation.

### Step 038

**SAY BEFORE:**

> I confirm that the batch should be committed to this institution.

**DO:** Click OK in the browser confirmation.

**WAIT FOR:** The page reports 65 created, 0 updated, 0 unchanged and 0 held.

**SAY AFTER THE RESULT:**

> The sixty-five admissions are now saved.

### Step 039

**SAY BEFORE:**

> I return to the overview to check the saved result.

**DO:** Click Back to overview.

**WAIT FOR:** College A's refreshed dashboard is loaded.

### Step 040

**SAY BEFORE:**

> The dashboard now shows sixty-five active admissions, sixty simulated identity matches, and five identity gaps.

**DO:** Point to Active admissions, Verified identities and Identity gaps.

**WAIT FOR:** The cards show Active admissions 65, Verified identities 60 and Identity gaps 5.

**SAY AFTER THE RESULT:**

> Missing identifiers remain visible and still count toward recorded intake.

### Step 041

**SAY BEFORE:**

> Computer Science has sixty-five active admissions against the configured limit of sixty.

**DO:** Point to Above basic intake and the Computer Science intake row.

**WAIT FOR:** Above basic intake shows 5.

**SAY AFTER THE RESULT:**

> This is a demo intake comparison, not an official regulatory finding.

### Step 042

**SAY BEFORE:**

> I open the category breakdown to see the retained admission flags.

**DO:** Expand Show category / supernumerary breakdown.

**WAIT FOR:** The category cards are visible.

**SAY AFTER THE RESULT:**

> Seat grouping and nationality flags are separate dimensions; adding every column would overcount students.

### Step 043

**SAY BEFORE:**

> I close the breakdown so we can focus on correcting a blocked admission next.

**DO:** Collapse Show category / supernumerary breakdown.

**WAIT FOR:** The dashboard is visible with the breakdown collapsed.

## Chapter 06 — Stage a file with structural errors

**Role:** College A · tab 1. **Purpose:** Make the held-work baseline visible before opening a correction case.

### Step 044

**SAY BEFORE:**

> I open a second submission to demonstrate a structural error.

**DO:** Click Upload admissions.

**WAIT FOR:** The upload form is loaded.

### Step 045

**SAY BEFORE:**

> I select the same academic year for this correction example.

**DO:** Open Academic year and choose 2026-27.

**WAIT FOR:** Academic year shows 2026-27.

### Step 046

**SAY BEFORE:**

> I choose the structural errors CSV, which contains three deliberately invalid synthetic rows.

**DO:** Select fixtures/structural-errors.csv in the Student CSV file control.

**WAIT FOR:** The upload area shows structural-errors.csv.

### Step 047

**SAY BEFORE:**

> I validate the second file before saving it.

**DO:** Click Validate and preview.

**WAIT FOR:** The structural-errors.csv review is loaded.

### Step 048

**SAY BEFORE:**

> This file has three rows and three blocking errors.

**DO:** Point to the summary cards and issue filters.

**WAIT FOR:** The report shows 3 submitted rows, 0 without issues, 0 warnings and 3 blocking errors.

**SAY AFTER THE RESULT:**

> These rows need correction before they can become admissions.

### Step 049

**SAY BEFORE:**

> I keep the mode that saves acceptable rows and holds structural errors.

**DO:** Scroll to Ready to save and keep Save acceptable rows; hold errors selected.

**WAIT FOR:** The selected commit mode is visible.

**SAY AFTER THE RESULT:**

> In this file every row is blocked, so no new admission will be created by this commit.

### Step 050

**SAY BEFORE:**

> I commit the reviewed batch so its blocked rows remain tracked as held work.

**DO:** Click Commit batch.

**WAIT FOR:** The browser confirmation appears.

### Step 051

**SAY BEFORE:**

> I confirm the commit.

**DO:** Click OK in the confirmation.

**WAIT FOR:** The result shows 0 created and 3 held.

**SAY AFTER THE RESULT:**

> The existing sixty-five admissions have not increased.

### Step 052

**SAY BEFORE:**

> I return to the overview to inspect the held work before correcting it.

**DO:** Click Back to overview.

**WAIT FOR:** The dashboard is loaded.

### Step 053

**SAY BEFORE:**

> There are two held admission candidates and one unassignable submitted row.

**DO:** Scroll to Data quality and point to held candidates and unassignable rows.

**WAIT FOR:** The panel shows 2 held admission candidates and 1 unassignable submitted row.

**SAY AFTER THE RESULT:**

> The unknown programme cannot yet be assigned to a known admission target.

### Step 054

**SAY BEFORE:**

> I reopen the structural errors submission to work on one specific candidate.

**DO:** In Recent submissions, click structural-errors.csv.

**WAIT FOR:** The original structural-errors.csv report is loaded.

### Step 055

**SAY BEFORE:**

> I filter the report to the invalid date.

**DO:** Click the Date invalid issue filter for DATE_INVALID.

**WAIT FOR:** The STU-080 row is visible.

**SAY AFTER THE RESULT:**

> This candidate has an invalid start date.

### Step 056

**SAY BEFORE:**

> I open a correction case for this specific issue.

**DO:** Click Open case for STU-080's DATE_INVALID issue.

**WAIT FOR:** The Resolution Desk shows Case for STU-080.

**SAY AFTER THE RESULT:**

> The Resolution Desk links this submitted issue to its next action and outcome.

## Chapter 07 — Preview, apply and verify the correction

**Role:** College A · tab 1. **Purpose:** Show a reviewed date change, successful save and current-work counts.

### Step 057

**SAY BEFORE:**

> I select Review a correction to edit the affected admission data.

**DO:** Click Review a correction in the STU-080 case.

**WAIT FOR:** The Correct this admission record dialog has loaded the current fields.

### Step 058

**SAY BEFORE:**

> I replace the invalid start date with the fifteenth of July, twenty twenty-six, using year-month-day format.

**DO:** In Start date, replace not-a-date with 2026-07-15.

**WAIT FOR:** Start date contains 2026-07-15.

### Step 059

**SAY BEFORE:**

> I preview the correction before applying it.

**DO:** Click Preview correction.

**WAIT FOR:** Review the exact proposed change is visible.

### Step 060

**SAY BEFORE:**

> The comparison shows the invalid value changing to the valid date.

**DO:** Point to the Start date comparison and the proposed outcome.

**WAIT FOR:** The proposal shows 1 new admission, 0 updated, 0 unchanged and active count change +1.

**SAY AFTER THE RESULT:**

> The preview explains the effect before the admission is saved.

### Step 061

**SAY BEFORE:**

> I apply the reviewed correction.

**DO:** Click Apply correction.

**WAIT FOR:** The dialog closes and the case is resolved.

**SAY AFTER THE RESULT:**

> The save succeeds, and the case records the correction outcome.

### Step 062

**SAY BEFORE:**

> I check the case history after the correction.

**DO:** Scroll to Case history in the same case.

**WAIT FOR:** The history includes the resolved state and applied correction.

**SAY AFTER THE RESULT:**

> The submitted issue and its resolution are traceable.

### Step 063

**SAY BEFORE:**

> I return to the overview to check the admission and held-work counts.

**DO:** Click Overview in the sidebar.

**WAIT FOR:** The College A dashboard is loaded.

### Step 064

**SAY BEFORE:**

> Active admissions have increased to sixty-six. Held admission candidates have fallen from two to one.

**DO:** Point to Active admissions and the held-work panel.

**WAIT FOR:** The dashboard shows 66 active admissions, 1 held admission candidate and 1 unassignable row.

**SAY AFTER THE RESULT:**

> The corrected candidate is no longer counted as unresolved held work.

## Chapter 08 — Show the retained report and the saved enrolment

**Role:** College A · tab 1. **Purpose:** Explain why historical errors remain while the current record is usable.

### Step 065

**SAY BEFORE:**

> I reopen the original submission to check what remains in its history.

**DO:** In Recent submissions, open structural-errors.csv.

**WAIT FOR:** The structural-errors.csv report is loaded.

### Step 066

**SAY BEFORE:**

> I return to the original invalid-date row.

**DO:** Click the Date invalid issue filter for DATE_INVALID.

**WAIT FOR:** STU-080 is marked Corrected and the original issue text is retained.

**SAY AFTER THE RESULT:**

> The report still describes the original upload. It has not been rewritten to pretend the error never existed.

### Step 067

**SAY BEFORE:**

> The original blocking-error summary is historical.

**DO:** Point to the original summary and the Corrected row together.

**WAIT FOR:** The report still shows its original three blocking errors, while STU-080 is marked Corrected.

**SAY AFTER THE RESULT:**

> Current held-work counts come from unresolved work, which is why the dashboard count fell.

### Step 068

**SAY BEFORE:**

> I open Enrolments to confirm the corrected candidate is now a saved record.

**DO:** Click Enrolments in the sidebar.

**WAIT FOR:** The enrolment list is loaded.

### Step 069

**SAY BEFORE:**

> I search for student reference eighty.

**DO:** Enter STU-080 in Student reference.

**WAIT FOR:** The list is filtered to STU-080.

### Step 070

**SAY BEFORE:**

> I open the saved enrolment.

**DO:** Click Demo Student 080 in the filtered row.

**WAIT FOR:** The record dialog shows the programme, masked identifier and recorded state.

**SAY AFTER THE RESULT:**

> The student now has a canonical admission record. The earlier blocked input remains in the correction case.

### Step 071

**SAY BEFORE:**

> I close the record details.

**DO:** Close the record dialog with its top-right X.

**WAIT FOR:** The enrolment list is visible.

**SAY AFTER THE RESULT:**

> Next I will introduce the second college's data so we can see how an overlap arises.

## Chapter 09 — Import the second college's records on screen

**Role:** College B · tab 3. **Purpose:** Show the second source of the overlap instead of relying on preloaded hidden data.

### Step 072

**SAY BEFORE:**

> I am now the administrator of Riverdale Technical College, our second demo institution.

**DO:** Switch to College B with Ctrl+3.

**WAIT FOR:** The Riverdale Overview is visible.

### Step 073

**SAY BEFORE:**

> Riverdale was approved earlier, but it has not imported admissions yet.

**DO:** Point to Riverdale's approval notice and Active admissions card.

**WAIT FOR:** The fresh dataset shows Demo approval active and 0 active admissions.

**SAY AFTER THE RESULT:**

> This is a separate institution account and dataset.

### Step 074

**SAY BEFORE:**

> I open Riverdale's Upload admissions page.

**DO:** Click Upload admissions.

**WAIT FOR:** The Riverdale upload form is loaded.

### Step 075

**SAY BEFORE:**

> I select the same academic year.

**DO:** Open Academic year and choose 2026-27.

**WAIT FOR:** Academic year shows 2026-27.

### Step 076

**SAY BEFORE:**

> I select the identity cases CSV for Riverdale.

**DO:** Choose fixtures/identity-cases.csv in the Student CSV file control.

**WAIT FOR:** The selected filename is identity-cases.csv.

**SAY AFTER THE RESULT:**

> One verified synthetic student in this file is also enrolled at Deccan Institute.

### Step 077

**SAY BEFORE:**

> I validate Riverdale's file.

**DO:** Click Validate and preview.

**WAIT FOR:** The identity-cases.csv review is loaded.

### Step 078

**SAY BEFORE:**

> The file has six rows: one without issues, five identity warnings, and no structural blocking errors.

**DO:** Point to the summary cards.

**WAIT FOR:** The cards show 6 submitted rows, 1 without issues, 5 warnings and 0 blocking errors.

**SAY AFTER THE RESULT:**

> The warnings remain visible for follow-up.

### Step 079

**SAY BEFORE:**

> I keep the mode that accepts structurally valid rows while retaining their identity warnings.

**DO:** Scroll to Ready to save and choose Save acceptable rows; hold errors.

**WAIT FOR:** The selected commit mode is visible.

### Step 080

**SAY BEFORE:**

> I commit Riverdale's reviewed submission.

**DO:** Click Commit batch.

**WAIT FOR:** The browser confirmation appears.

### Step 081

**SAY BEFORE:**

> I confirm the Riverdale commit.

**DO:** Click OK in the confirmation.

**WAIT FOR:** The result shows 6 created and 0 held.

**SAY AFTER THE RESULT:**

> These are Riverdale's admissions, separate from Deccan's sixty-six records.

### Step 082

**SAY BEFORE:**

> I return to Riverdale's overview.

**DO:** Click Back to overview.

**WAIT FOR:** The overview shows 6 active admissions.

**SAY AFTER THE RESULT:**

> Both colleges have now submitted the shared student's enrolment. I will switch to the officer to review the date overlap.

## Chapter 10 — Review the overlap as an officer

**Role:** Officer · tab 2. **Purpose:** Connect the visible two-college import to a human review rather than an automatic rejection.

### Step 083

**SAY BEFORE:**

> I return to the officer workspace to inspect the combined result.

**DO:** Switch to the Officer tab with Ctrl+2.

**WAIT FOR:** The officer account is visible.

### Step 084

**SAY BEFORE:**

> I open Admission oversight.

**DO:** Click Overview in the sidebar.

**WAIT FOR:** The officer overview is loaded.

### Step 085

**SAY BEFORE:**

> I refresh the overview after both colleges' commits.

**DO:** Click Refresh overview.

**WAIT FOR:** The officer metrics update.

**SAY AFTER THE RESULT:**

> The officer can now see both institutions' recorded admissions.

### Step 086

**SAY BEFORE:**

> There are two colleges, seventy-two active admissions, and one overlap awaiting review.

**DO:** Point to Colleges in view, Active admissions and Overlaps awaiting review.

**WAIT FOR:** The fresh dataset shows 2 colleges, 72 active admissions and 1 open overlap.

**SAY AFTER THE RESULT:**

> Seventy-two counts enrolments, not seventy-two distinct people.

### Step 087

**SAY BEFORE:**

> I open the overlap review queue.

**DO:** Click Open overlap reviews.

**WAIT FOR:** Review overlapping enrolments is loaded with Needs review selected.

### Step 088

**SAY BEFORE:**

> The review brings together the two enrolments linked to the same simulated verified identity.

**DO:** Point to the two college records in the same review.

**WAIT FOR:** Both Deccan and Riverdale appear with overlapping date intervals.

**SAY AFTER THE RESULT:**

> This overlap needs investigation. It does not by itself prove fraud or an invalid admission.

### Step 089

**SAY BEFORE:**

> I open the decision form after comparing the evidence.

**DO:** Click Review this overlap.

**WAIT FOR:** The Record a review decision dialog is open.

### Step 090

**SAY BEFORE:**

> I select More evidence needed because the date intersection alone does not settle the case.

**DO:** Choose More evidence needed under Review outcome.

**WAIT FOR:** Review outcome shows More evidence needed.

### Step 091

**SAY BEFORE:**

> I save that review outcome.

**DO:** Click Save review.

**WAIT FOR:** The dialog closes and the page confirms Review saved: More evidence needed.

**SAY AFTER THE RESULT:**

> Both admission records remain unchanged.

### Step 092

**SAY BEFORE:**

> I filter to More evidence needed to find the recorded decision.

**DO:** Choose More evidence needed under the Review status filter.

**WAIT FOR:** The escalated review is visible.

**SAY AFTER THE RESULT:**

> The item remains available for follow-up rather than being treated as an automatic rejection.

## Chapter 11 — Inspect activity and check its integrity

**Role:** Officer · tab 2. **Purpose:** Show accountability immediately after the officer's decision.

### Step 093

**SAY BEFORE:**

> I open Activity history to inspect the actions recorded during this workflow.

**DO:** Click Activity history in the sidebar.

**WAIT FOR:** The activity table and Check history integrity panel are loaded.

### Step 094

**SAY BEFORE:**

> The history records actions such as batch commits, corrections, approvals and review decisions.

**DO:** Point to the recent activity rows.

**WAIT FOR:** Actual recorded entries and their actor/time are visible.

**SAY AFTER THE RESULT:**

> This gives staff a way to investigate who changed what.

### Step 095

**SAY BEFORE:**

> I run the integrity check on the retained audit history.

**DO:** Click Run integrity check.

**WAIT FOR:** The check completes and reports its result.

### Step 096

**SAY BEFORE:**

> The check has passed for the retained events shown here.

**DO:** Hold on the successful integrity result.

**WAIT FOR:** The page states Integrity check passed.

**SAY AFTER THE RESULT:**

> This checks the stored chain; it does not make the whole database tamper-proof.

### Step 097

**SAY BEFORE:**

> I open the check's details and limits.

**DO:** Expand Check details and limits.

**WAIT FOR:** The digest summary, legacy snapshot count and scope statement are visible.

**SAY AFTER THE RESULT:**

> The interface explains what the check can establish and where its limits remain.

## Chapter 12 — Open the student's records and personal card

**Role:** Student · tab 4. **Purpose:** Continue with the shared student's own account and choose exactly one college record.

### Step 098

**SAY BEFORE:**

> I am now signed in as synthetic student one, the student whose records were submitted by both colleges.

**DO:** Switch to the Student tab with Ctrl+4.

**WAIT FOR:** The Student workspace is visible.

### Step 099

**SAY BEFORE:**

> I refresh the student's view after the college submissions.

**DO:** Click Refresh.

**WAIT FOR:** The student's record queries have completed.

### Step 100

**SAY BEFORE:**

> I open My records to choose the record to share.

**DO:** Click My records in the sidebar.

**WAIT FOR:** The page shows Computer Science records for Deccan and Riverdale.

**SAY AFTER THE RESULT:**

> Each college's enrolment is shown separately.

### Step 101

**SAY BEFORE:**

> I open the student card for the Deccan record.

**DO:** On Deccan Institute of Technology's record, click View student card.

**WAIT FOR:** Your student card is open for Deccan Institute.

### Step 102

**SAY BEFORE:**

> The card summarises this enrolment and the student's workspace account.

**DO:** Point to the card's course, institution, academic year, admission state and masked APAAR.

**WAIT FOR:** The card shows DEMO RECORD and Simulated match.

**SAY AFTER THE RESULT:**

> It is a personal record summary, not an official APAAR identity document or certificate.

### Step 103

**SAY BEFORE:**

> I close the card and return to the same Deccan record.

**DO:** Close Your student card with its top-right X.

**WAIT FOR:** My records is visible.

### Step 104

**SAY BEFORE:**

> I start sharing this specific Deccan record.

**DO:** On the Deccan record, click Start sharing.

**WAIT FOR:** The Share your student record dialog displays a request code.

**SAY AFTER THE RESULT:**

> Creating the code does not reveal the academic record.

### Step 105

**SAY BEFORE:**

> I copy the one-use request code for the verifier.

**DO:** Click Copy request code.

**WAIT FOR:** The button shows Copied.

**SAY AFTER THE RESULT:**

> The verifier can use this code to ask for permission. It expires after fifteen minutes.

### Step 106

**SAY BEFORE:**

> I close the dialog while keeping the request code in the clipboard.

**DO:** Close Share your student record with its top-right X.

**WAIT FOR:** My records is visible.

**SAY AFTER THE RESULT:**

> I will now act as the verifier who received that code.

## Chapter 13 — Submit a specific request as the verifier

**Role:** Verifier · tab 5. **Purpose:** Show exactly what is requested before the student decides.

### Step 107

**SAY BEFORE:**

> I am now using the approved demo verifier's account.

**DO:** Switch to the Verifier tab with Ctrl+5.

**WAIT FOR:** The Verifier workspace is visible.

### Step 108

**SAY BEFORE:**

> I open Request access to ask for specific information.

**DO:** Click Request access in the sidebar.

**WAIT FOR:** The Request student permission form is loaded.

### Step 109

**SAY BEFORE:**

> I paste the student's request code into the labelled field.

**DO:** Paste the copied code into Student request code.

**WAIT FOR:** The code field contains the pasted value; keep it masked and do not read it aloud.

### Step 110

**SAY BEFORE:**

> I choose Admission confirmation as the reason for the request.

**DO:** Open Purpose and choose Admission confirmation.

**WAIT FOR:** Purpose shows Admission confirmation.

### Step 111

**SAY BEFORE:**

> I request the programme field.

**DO:** Check Programme in Choose fields to request.

**WAIT FOR:** Programme is checked.

### Step 112

**SAY BEFORE:**

> I also request the institution field.

**DO:** Check Institution in Choose fields to request.

**WAIT FOR:** Programme and Institution are the only two selected fields.

### Step 113

**SAY BEFORE:**

> I send these two field requests to the student.

**DO:** Click Send approval request.

**WAIT FOR:** The page shows Request submitted.

**SAY AFTER THE RESULT:**

> This submits a permission request. It does not disclose either record value.

### Step 114

**SAY BEFORE:**

> I open the request history to check the submission.

**DO:** Click Track your requests in the submission acknowledgement.

**WAIT FOR:** Your request history shows the pending request, purpose and requested field names.

**SAY AFTER THE RESULT:**

> The verifier still cannot see the student's unapproved record values.

## Chapter 14 — Approve fewer fields as the student

**Role:** Student · tab 4. **Purpose:** Make the student's choice, recipient and duration explicit.

### Step 115

**SAY BEFORE:**

> I return to the student account to review that request.

**DO:** Switch back to the Student tab with Ctrl+4.

**WAIT FOR:** The Student workspace is visible.

### Step 116

**SAY BEFORE:**

> I open Requests.

**DO:** Click Requests in the sidebar.

**WAIT FOR:** The Review requests page is loaded.

### Step 117

**SAY BEFORE:**

> I refresh the inbox to load the verifier's new request.

**DO:** Click Refresh.

**WAIT FOR:** The pending Admission confirmation request is visible.

### Step 118

**SAY BEFORE:**

> The student can see the demo admissions verifier, its admission-confirmation purpose, and the Deccan record it wants to check.

**DO:** Point to the requester, purpose and Your record fields.

**WAIT FOR:** The request names the expected organisation and Deccan record.

**SAY AFTER THE RESULT:**

> It asks for Programme and Institution, but neither field is preselected for approval.

### Step 119

**SAY BEFORE:**

> I approve Programme only and leave Institution unchecked.

**DO:** Check Programme only under Choose what to share.

**WAIT FOR:** Exactly one field is selected.

**SAY AFTER THE RESULT:**

> The student can approve less than the verifier requested.

### Step 120

**SAY BEFORE:**

> I set the sharing period to fifteen minutes.

**DO:** Open Allow access for and choose 15 minutes.

**WAIT FOR:** Allow access for shows 15 minutes.

**SAY AFTER THE RESULT:**

> This is a time-limited grant, and the student can stop it earlier.

### Step 121

**SAY BEFORE:**

> I approve the selected field for this verifier.

**DO:** Click Approve selected fields.

**WAIT FOR:** The app moves to Shared access and shows Your consent link.

**SAY AFTER THE RESULT:**

> The app opens Shared access and displays the new sharing card.

### Step 122

**SAY BEFORE:**

> The card identifies the intended verifier, the one approved field, and the expiry.

**DO:** Point to the sharing card's recipient, Programme field, expiry and QR.

**WAIT FOR:** The card lists Programme only and says verifier sign-in is required.

**SAY AFTER THE RESULT:**

> The QR and link represent the same limited permission; they do not publish the complete record.

### Step 123

**SAY BEFORE:**

> I copy the consent link for the intended verifier.

**DO:** Click Copy consent link.

**WAIT FOR:** The button shows Link copied.

**SAY AFTER THE RESULT:**

> I will keep this same link for the verification and revocation checks.

## Chapter 15 — Open only the approved field as the verifier

**Role:** Verifier · tab 5. **Purpose:** Show the actual returned value and the absent unapproved field.

### Step 124

**SAY BEFORE:**

> I return to the same verifier account that requested access.

**DO:** Switch to the Verifier tab with Ctrl+5.

**WAIT FOR:** The Verifier workspace is visible.

### Step 125

**SAY BEFORE:**

> I open Verify a link.

**DO:** Click Verify a link in the sidebar.

**WAIT FOR:** The Open an approved link page is loaded.

### Step 126

**SAY BEFORE:**

> I paste the student's approved link into the labelled field.

**DO:** Paste the copied link into Student consent link.

**WAIT FOR:** The link field is filled and remains masked.

### Step 127

**SAY BEFORE:**

> I select Verify approved fields to check the current permission and open its allowed data.

**DO:** Click Verify approved fields.

**WAIT FOR:** The result panel shows Approved fields.

### Step 128

**SAY BEFORE:**

> The result contains Computer Science as the programme.

**DO:** Point to Programme: Computer Science in the result.

**WAIT FOR:** Programme is the only returned field.

**SAY AFTER THE RESULT:**

> The institution name is absent because the student did not approve it, even though the verifier originally requested it.

## Chapter 16 — Stop sharing and prove the same link is refused

**Role:** Student → Verifier → Student. **Purpose:** Demonstrate revocation, a genuine retry, and the student's access history.

### Step 129

**SAY BEFORE:**

> I return to the student to stop this sharing grant.

**DO:** Switch to the Student tab with Ctrl+4.

**WAIT FOR:** The student's Shared access page is visible.

### Step 130

**SAY BEFORE:**

> I select Stop sharing on this verifier's grant.

**DO:** Scroll to the grant for Demo admissions verifier and click Stop sharing.

**WAIT FOR:** The Stop sharing this record? confirmation dialog is open.

### Step 131

**SAY BEFORE:**

> I confirm that future checks through this grant should stop.

**DO:** Click Confirm stop sharing.

**WAIT FOR:** The dialog closes, the grant says Sharing stopped, and the displayed new-link card disappears.

**SAY AFTER THE RESULT:**

> The stop-sharing decision has been saved.

### Step 132

**SAY BEFORE:**

> I return to the verifier to test the same link again.

**DO:** Switch to the Verifier tab with Ctrl+5.

**WAIT FOR:** The verifier's previous result may still be visible.

**SAY AFTER THE RESULT:**

> Stopping future access cannot erase information that was already viewed.

### Step 133

**SAY BEFORE:**

> I clear the earlier result before making another request.

**DO:** If the previous Approved fields panel is visible, click Hide result. Otherwise hold on the empty result area.

**WAIT FOR:** The previous result is hidden or already cleared.

### Step 134

**SAY BEFORE:**

> I paste the exact same link used in the successful check.

**DO:** Paste the same consent link from the clipboard into Student consent link.

**WAIT FOR:** The same link is present in the masked field.

### Step 135

**SAY BEFORE:**

> I try to verify through that link again after revocation.

**DO:** Click Verify approved fields.

**WAIT FOR:** The page shows This link cannot be opened.

**SAY AFTER THE RESULT:**

> This new attempt is refused. The earlier permission no longer allows another check.

### Step 136

**SAY BEFORE:**

> I return to the student to inspect the access record.

**DO:** Switch back to the Student tab with Ctrl+4.

**WAIT FOR:** The Student workspace is visible.

### Step 137

**SAY BEFORE:**

> I open Access history.

**DO:** Click Access history in the sidebar.

**WAIT FOR:** The Access history page is loaded.

### Step 138

**SAY BEFORE:**

> I refresh the recorded accesses.

**DO:** Click Refresh.

**WAIT FOR:** The completed verifier access entry is loaded.

### Step 139

**SAY BEFORE:**

> The history shows which verifier opened the approved field, for what purpose, and when.

**DO:** Point to the verifier organisation, Programme field, purpose and time.

**WAIT FOR:** The entry names the demo admissions verifier and Programme.

**SAY AFTER THE RESULT:**

> This gives the student visibility into the successful access. The revoked grant still cannot be used again.

## Chapter 17 — Close the story

**Role:** Student · tab 4. **Purpose:** Finish with the user value of the completed workflow.

### Step 140

**SAY BEFORE:**

> I return to the student overview to close the demonstration.

**DO:** Click Overview in the student sidebar.

**WAIT FOR:** Your student records is visible.

### Step 141

**SAY BEFORE:**

> We have followed the complete path: institution approval, admission validation, correction, officer review, and student-controlled verification. APAAR Workspace uses Python, FastAPI, PostgreSQL, and React to connect these tasks in one workflow. This is our synthetic prototype for SIH26263; official AICTE and APAAR integration remain future work.

**DO:** Hold on the overview and add the APAAR Workspace / SIH26263 closing overlay in the editor.

**WAIT FOR:** End the recording after the closing line; leave the synthetic-demo label visible.

## When the screen differs from the script

Pause the recording at the current step. Resume only after the visible state matches the narration. Failed or loading results are not evidence for a success statement.

| Situation | What to do before continuing |
|---|---|
| Database does not exist | Complete the CREATE DATABASE step on the same PostgreSQL server, confirm the name in private settings, then run migrations. Preserve existing databases. |
| College already approved | Its first-approval state has already been consumed. Use a new separate recording database for the exact script, or record a clearly stated history walkthrough instead. Do not suspend it merely to imitate first approval. |
| CSV result says updated or unchanged | Existing canonical records are present. The exact new-admission counts require the fresh dataset. Preserve that dataset and use another new recording target. |
| STU-080 is already resolved | Show its real history with past-tense narration, or use a fresh recording database. Do not claim that applying again created another admission. |
| Officer shows no overlap | Confirm both College A and College B imports were committed for 2026-27, then use Refresh overview / Refresh reviews. The second college is imported on screen in Chapter 09, not during preparation. For genuinely older records, see the documented explicit backfill in the operator guide. |
| Student does not show Deccan | Use the Student tab, My records and Refresh. Confirm student1 and a successful Deccan intake-65 commit. Do not choose Riverdale merely because it appears first. |
| Request not in the student's inbox | Select Requests and Refresh; check that the request used a fresh one-use code for the Deccan record and the intended verifier. |
| Request code expired or was used | Start sharing again for Deccan, copy the new code and record the verifier request again. Do not reuse a consumed handle. |
| Clipboard lost the consent link | Use the displayed Copy consent link before leaving while it is available. If it is lost later, pause and follow the product's explicit Replace lost link flow, then record a fresh coherent consent/resolve/revoke segment. Do not invent or reconstruct a token. |
| Consent expired before revocation test | A refusal cannot prove revocation if the grant had already expired. Record a fresh segment with the stated 15-minute period and perform the successful check and revoke/retry while it is still live. |
| Native dialog or file picker takes longer | Leave a quiet pause; trim that dead time later. Speak the result only once the expected state is visible. |
| API, permission, integrity or correction error | Stop the success narration and retain the error/request ID for troubleshooting. Do not read the next success line over the error. |

## Editing and export

- Capture a readable browser window in OBS at 1080p and 30 fps. Keep microphone audio for live narration. If adding a separate voice track, mute the capture's microphone/desktop audio to prevent duplicate speech.
- Put a small role caption at role changes: **College A**, **Officer**, **College B**, **Student**, **Verifier**. The spoken transition explains why the role changes.
- Keep a short still or quiet pause on each result while its after-result line is spoken. Cut preparation, passwords, long file-picker delays and chapter-break silence.
- Use clip numbers rather than fixed timestamps to keep the sequence intact. In Clipchamp, place each matching chapter's narration under its chapter's screen clip, then align the step/result phrases.
- OBS MKV recordings can be converted with **File → Remux Recordings** before importing MP4 into the editor. Export 1080p MP4 and review the whole result.
- There is no imposed runtime or overall character cap for this detailed version. If a later submission requires a shorter video, make a separate abridged edit after this complete walkthrough is coherent.

## Final human check

- [ ] Each spoken action appears on screen, in the numbered order.
- [ ] Each after-result line follows an actually loaded result.
- [ ] Both institutions were approved visibly and all three CSV imports were shown.
- [ ] College B was introduced before its record caused the overlap review.
- [ ] The correction shows its baseline, preview, application, updated count and retained report.
- [ ] Every role switch is named and uses the intended authenticated account.
- [ ] Student one shares the Deccan record; the verifier requests two fields and receives only Programme.
- [ ] The 15-minute grant is still live at the successful check and is then revoked before the retry.
- [ ] The retry uses the exact same link and is refused; the successful prior access is visible in history.
- [ ] No passwords, connection strings, private configuration or real student data appear.
- [ ] The full export has been watched for continuity, legibility and audio alignment.

These are recording/review tasks, not automatic claims of completed human work. Documentation validation checks the step/narration mapping, labels, source fixtures and links. Existing application-test evidence is in the [progress checklist](05-progress-checklist.md); this document does not claim that the user's Windows recording or a hosted walkthrough has been performed.
