---
type: Demo Recording Script
title: Final voice-over and screen recording guide
description: A synchronized eleven-scene demo with narration under 5000 characters, including synthetic institution approval.
tags: [apaar, demo, recording, voiceover, sih]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-28T04:21:10Z"}
sources:
  - resource: 12-demo-walkthrough.md
  - resource: 13-demo-interface.md
  - resource: 15-institution-approval-demo.md
  - resource: 05-progress-checklist.md
---

# 14 — Final voice-over and recording guide

**Estimated screen runtime: 7:10. Hard stop: 8:30, including title and outro.** A shorter edit is welcome. These are planning cues, not measured human speech or a completed recording. Use the actual voice track to align the footage.

The [final narration-only file](demo-voiceover.txt) contains **4,101 characters, including spaces, LF line breaks and the final newline**, and **607 whitespace-separated words**. Its content is ASCII, so UTF-8 bytes, Unicode characters and UTF-16 code units have the same count. It stays below 5,000 even with Windows CRLF line endings. The 5,000-character limit applies to the spoken script, not this preparation guide.

At 115–130 words/minute, narration takes about 4:40–5:17; the timeline leaves the rest for screen actions and pauses. Each of the eleven paragraphs in the text file matches the same numbered scene below. Read only the blockquoted voice-over, not titles, timings or screen cues. The opening takes about 25–30 seconds; the full problem title stays on screen. The other ten narration paragraphs are unchanged. Institution approval remains its own scene.

## 1. Prepare the application outside the video

Use local recording if it works reliably; Vercel is optional. For a hosted recording, the frontend must reach the hosted Python API and PostgreSQL, with HTTPS, the correct API URL and exact allowed frontend origin configured. Confirm the full journey on that deployment first. Keep the same simulated-evidence wording in either setup.

Stop both servers before updating. From your actual repository root:

```powershell
Set-Location D:\Projects\appar-id\appar-id
git pull --ff-only
Set-Location backend
uv run --frozen python ../scripts/configure_extensions.py --enable-audit --enable-consent
```

Run the helper from **backend** so `../scripts/` resolves correctly. It preserves existing secrets and passwords. Keep both servers stopped while selecting the database in the next section. Keep `MOCK_REGISTRY_OUTAGE=false` in private local settings.

## 2. Choose data without deleting existing work

**Primary sequence:** use a separate, empty synthetic recording database so College A starts without admissions or approval. Do not delete rows, truncate tables, drop the current database, or edit audit history to recreate an initial state. If you already imported data, either use the alternatives below or create a new database.

To create a separate target, stop the backend. In TablePlus connect as administrator `postgres` to database `postgres` at `127.0.0.1:5432`, then run:

```sql
CREATE DATABASE apaar_recording_final OWNER apaar_app;
```

If that name already exists, choose a new name; preserve the existing target. In the root `.env`, change **only the database name in `DATABASE_URL`** to the new target. Preserve username, password, host, port, options and every key. Leave `TEST_DATABASE_URL` unchanged. Do not share the connection string.

After choosing either the existing database or the separate new target, run from the correct folder:

```powershell
Set-Location D:\Projects\appar-id\appar-id\backend
uv run --frozen alembic upgrade head
uv run --frozen python -m app.seed --demo
```

The seed creates missing accounts/programmes, preserves existing data, and never approves institutions or imports admissions. New accounts use the current private `DEMO_PASSWORD`; existing accounts keep their prior password.

Start the backend and frontend in separate PowerShell terminals:

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

From another terminal, check local health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expect API/database `ok`, registry `simulated`, audit enabled and consent enabled. Complete login before recording. Keep terminals, passwords and `.env` out of the video. If you switched to a separate recording target, after recording stop the backend, restore the original database name and restart to return to the preserved original dataset.

## 3. Stage the colleges and role tabs

Before recording:

1. Sign in as `officer@example.test`. Open **Institution approval**, choose **2026-27**, and approve **Riverdale Technical College / College B only** after reviewing its synthetic evidence. Leave **Deccan Institute of Technology / College A** pending for scene 2.
2. Sign in as `collegeb@example.test`. Upload and commit `fixtures/identity-cases.csv` for **2026-27**, then sign out. This prepares the second college's record; the officer overlap appears after College A commits its matching person during scene 4.
3. Open one clean browser window with the four tabs below. Sign in shortly before recording, using the local demo password. Each tab keeps its own in-memory session; do not reload it. A reload requires signing in again. Switch tabs using **Ctrl+1** through **Ctrl+4**.

| Tab | Account | Starting page |
|---|---|---|
| 1 — College A | `collegea@example.test` | Overview or Upload admissions; still pending approval |
| 2 — Officer | `officer@example.test` | Institution approval; College A pending, College B approved |
| 3 — Student | `student1@example.test` | My records; refresh after College A commits |
| 4 — Verifier | `verifier1@example.test` | Request access |

Keep `fixtures/intake-65.csv` and `fixtures/structural-errors.csv` easy to select. Do not approve College A or apply STU-080's final repair during rehearsal on the only dataset you intend to film. Rehearse on a separate dataset, or use the existing-data alternatives. Ensure the officer can run the integrity check. Use in-app Refresh actions; wait for actual loaded results.

## 4. Capture and edit on Windows

1. Use OBS Studio to capture the browser window at **1920×1080 and 30 fps**. Close unrelated browser tabs and mute notifications. Use a readable browser zoom; take a ten-second test to check labels, cursor and dropdowns.
2. If your voice-over is already recorded, disable the OBS microphone and desktop audio. If recording live narration, keep the microphone on and avoid adding a second copy of the same audio in the editor.
3. For a separate voice track, record screen actions in scene order. Hold each important result for two or three seconds. Keep approval, commit, correction and revocation outcomes truthful; do not fabricate counters or turn an already-completed action into a new one.
4. OBS can record MKV and use **File → Remux Recordings** to create MP4. Import the screen footage and voice-over into Clipchamp. Put the voice track on the timeline first, split the footage at the scene boundaries, and align actions to the matching phrases rather than forcing speech to match estimated timestamps.
5. Trim file-picker delays, dead time and long tab switches. Record the request → approval → verification → revocation sequence together; the chosen grant lasts five minutes. Avoid unnecessary speed changes, keep the result screens readable, and include title/outro time in the limit.
6. Export **1080p MP4**. Watch the whole export once. Keep the final file below **8:30**; do not add an extra tour after the closing line.

If you already recorded an earlier narration, keep matching sections and replace only the lines that differ. The approval paragraph below is a short standalone pickup. If you keep the old audio unchanged, show the same approval actions during the problem introduction with this caption: **Officer reviews synthetic institution/year/programme evidence before enabling admissions.** Do not include both the caption-only version and a second full approval scene.

## 5. Running order

| Time | Scene | Screen |
|---|---|---|
| 00:00–00:30 | 1. SIH problem and quick introduction | Title slide → College A |
| 00:30–01:10 | 2. Institution approval before admissions | College A → Officer → College A |
| 01:10–01:50 | 3. Upload and understand the dry run | College A → Upload admissions |
| 01:50–02:25 | 4. Commit and read the dashboard | College A → Commit batch → Overview |
| 02:25–03:25 | 5. Correct a held row and retain its history | College A → Upload admissions → Resolution Desk |
| 03:25–04:00 | 6. Officer review of overlapping enrolments | Officer → Overlap reviews |
| 04:00–04:20 | 7. Check audit integrity | Officer → Activity history |
| 04:20–04:55 | 8. Student records, personal card, and request code | Student → My records |
| 04:55–06:10 | 9. Student-approved fields, sharing card, and verifier result | Verifier → Student → Verifier |
| 06:10–06:45 | 10. Revoke the grant and inspect access history | Student → Verifier → Student |
| 06:45–07:10 | 11. Close with implemented value | Student overview or officer overview |

## 6. Exact narration and matching screen actions

### Scene 1 · 00:00–00:30 — SIH problem and quick introduction

**On screen:** Title slide → College A.

- Show **SIH 2026 · AICTE · SIH26263** and **APAAR Workspace** immediately. Keep the full problem-statement title on screen; the voice-over uses the short reference.
- Display the full title: **Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions**.
- Move to College A's overview or Upload admissions page while explaining the issue. Keep the demo/simulated label visible and enter the live workflow by 00:30.
- Leave College A unreviewed for the next scene. This section explains the problem without asserting that the official APAAR platform failed.

**Voice-over — read this:**

> This is APAAR Workspace, our prototype for Smart India Hackathon 2026, AICTE problem statement SIH26263. Missing IDs and incorrect records complicate admissions. We help colleges check and correct data, while students control record sharing. Let's see it in action using synthetic data and simulated checks.

### Scene 2 · 00:30–01:10 — Institution approval before admissions

**On screen:** College A → Officer → College A.

- College A, tab 1: Upload admissions → choose **2026-27** and `fixtures/intake-65.csv` → **Validate and preview**. Hold briefly on the actual approval-required error. No admission batch is created by this refused request.
- Officer, tab 2: **Institution approval → 2026-27** → locate **Deccan Institute of Technology** → **Review demo evidence**.
- Show the synthetic institution ID, campus, approval reference, validity and matching programme intakes. Check **I reviewed the synthetic evidence and matching programmes** → **Approve demo access**.
- College A, tab 1: **View approval → Refresh approvals** to show the active demo status, then return to **Upload admissions**. This avoids waiting for the notice's 15-second automatic update. College B must already have been approved during preparation.
- If College A was already approved, use the existing-data alternative below. Do not suspend it merely to pretend this is its first approval.

**Voice-over — read this:**

> First, the college needs approval for admission submissions. An unreviewed college is blocked. The officer reviews the institution, academic year, validity, and programme intake against a synthetic catalogue. After the officer approves the matching evidence, demo submissions are enabled. Colleges cannot approve themselves. This demonstrates the approval control; it does not verify actual AICTE approval.

### Scene 3 · 01:10–01:50 — Upload and understand the dry run

**On screen:** College A → Upload admissions.

- College A: select **2026-27**, choose `fixtures/intake-65.csv` again, then **Validate and preview**.
- Show the intended file's **65 rows / 60 without issues / 5 warnings / 0 blocking errors**. These are file-validation counts; overall admission totals depend on existing data.
- Filter **APAAR missing**. Point to the explanation and separate **Open case** action. Optionally open **Why this issue?** briefly, then close it. Leave missing-ID cases unopened for this scene.

**Voice-over — read this:**

> The college administrator selects the academic year and uploads a CSV. A dry run checks the file without changing admissions. The preview separates acceptable rows, warnings, and blocking errors. Each issue explains what happened and what to do next. Missing APAAR identifiers remain visible as identity gaps, rather than removing students from the workflow.

### Scene 4 · 01:50–02:25 — Commit and read the dashboard

**On screen:** College A → Commit batch → Overview.

- Keep **Save acceptable rows; hold errors** selected → **Commit batch** → accept the confirmation.
- Select **Back to overview**. Point to Active admissions, Identity gaps, Above basic intake, and held work.
- On a clean College A dataset the result is 65 active admissions and 5 identity gaps. The voice-over deliberately avoids fixed dashboard totals. Briefly show the category breakdown only if time allows.

**Voice-over — read this:**

> After reviewing the preview, the administrator commits the acceptable rows. The dashboard separates active admissions, identity gaps, intake warnings, and held candidates. A missing identifier and a structurally invalid row are different problems. Keeping them separate helps the college understand its intake and the work that remains.

### Scene 5 · 02:25–03:25 — Correct a held row and retain its history

**On screen:** College A → Upload admissions → Resolution Desk.

- College A: upload `fixtures/structural-errors.csv` for **2026-27**, validate, then commit acceptable rows. Its three held rows comprise two held candidates and one unassignable row.
- Open the **DATE_INVALID** case for **STU-080**. In the Resolution Desk select **Review a correction**.
- Change **Start date** to **2026-07-15** → **Preview correction**. Show the before/after field and the intake effect.
- Select **Apply correction**. Show the resolved case, then Overview's Held Candidates count. On the clean dataset it falls **2 → 1**, and one admission is created.
- Open the original batch report if time allows: its original issue remains, with the corrected source row no longer counted as held work. If STU-080 was already repaired, use the historical-case alternative below.

**Voice-over — read this:**

> Now we open a row blocked by an invalid date. The administrator creates a case in the Resolution Desk, enters a correction, and previews the change before applying it. The system checks whether the underlying record has changed since that preview. After a successful correction, the admission is saved, the case resolves, and that row stops counting as held work. The original validation report remains available, preserving the initial issue and the correction history.

### Scene 6 · 03:25–04:00 — Officer review of overlapping enrolments

**On screen:** Officer → Overlap reviews.

- Officer tab: Overview → **Refresh overview** → **Open overlap reviews**. The overlap appears after College A's commit because College B's fixture was prepared earlier.
- Select **Review this overlap**; compare Deccan Institute and Riverdale Technical College's date intervals.
- Set **Review outcome → More evidence needed** → **Save review**. Show the saved result. Use **All reviews** to locate a previously reviewed item if needed.
- Both admission records remain. Do not describe the overlap as proven fraud or an automatic rejection.

**Voice-over — read this:**

> The officer workspace highlights enrolments linked to the same verified person with overlapping dates. An overlap is a reason to review evidence, not an automatic fraud finding. The officer compares the records and records an outcome. Here, we select More evidence needed. Both admission records remain available, and the decision is recorded for follow-up.

### Scene 7 · 04:00–04:20 — Check audit integrity

**On screen:** Officer → Activity history.

- Officer: **Activity history → Run integrity check**.
- Hold on the successful result. Leave technical details collapsed unless ahead of schedule.
- The scene demonstrates a check on the retained audit history, with its documented limits. Do not describe it as tamper-proof storage.

**Voice-over — read this:**

> Important actions produce audit events. The integrity check verifies the retained audit chain and can detect changes to that recorded history. This supports accountability, with the check's limits explained in the interface.

### Scene 8 · 04:20–04:55 — Student records, personal card, and request code

**On screen:** Student → My records.

- Student tab: use the in-app **Refresh** action so College A's newly committed record appears. Open **My records** and choose **Deccan Institute of Technology**.
- Select **View student card**; show the course, college, academic year, admission state and masked APAAR, then close the card.
- For that same Deccan record, select **Start sharing → Copy request code**. Close the dialog after copying. The request code expires after 15 minutes and can create one request.
- Do not reload the browser tab or paste the code into the address bar.

**Voice-over — read this:**

> The student workspace answers three questions: What records do I have? Who wants access? What have I shared? The student card summarises the course, college, academic year, admission state, and masked APAAR identifier. It is a workspace summary, not an official identity credential. To begin sharing, the student creates a temporary request code. Giving someone this code does not disclose the record.

### Scene 9 · 04:55–06:10 — Student-approved fields, sharing card, and verifier result

**On screen:** Verifier → Student → Verifier.

- Verifier tab: **Request access** → paste the copied code → choose **Admission confirmation** → select **Programme** and **Institution** → **Send approval request**.
- Student tab: **Requests → Refresh**. Show the recipient, purpose and requested fields. Select **Programme only**, choose **5 minutes**, then **Approve selected fields**.
- The student moves to **Shared access**. Show the new sharing card, intended recipient, Programme field, expiry and QR. Select **Copy consent link**.
- Verifier tab: **Verify a link** → paste into **Student consent link** → **Verify approved fields**. Show the result containing **Programme only**.
- Use the labelled field; opening the link directly would require verifier sign-in after fragment capture. Keep this same link in the clipboard for the next scene. Record this and the next scene together so the five-minute grant remains live until revocation.

**Voice-over — read this:**

> The verifier enters the code, selects a purpose, and requests Programme and Institution. The student sees who is asking, why, and which fields they want. Nothing is preselected. Here, the student approves only Programme for five minutes. The sharing card shows the intended recipient, approved fields, expiry, and a QR code with a copyable link. When the intended verifier opens the link and signs in, the system checks the grant again. The result contains only the programme. The institution was requested but was not approved, so it is not returned.

### Scene 10 · 06:10–06:45 — Revoke the grant and inspect access history

**On screen:** Student → Verifier → Student.

- Student: **Shared access → Stop sharing → Confirm stop sharing**.
- Verifier: submit the **same link** again with **Verify approved fields**. Show **This link cannot be opened**.
- Student: **Access history** → wait for the actual entry showing the verifier organisation, Programme field and access time.
- Stopping access prevents later checks through this grant; it cannot retract information the recipient has already received.

**Voice-over — read this:**

> The student can stop sharing before expiry. After revocation, another attempt to use the same link is denied. Access history shows the recorded verification access. This helps the student understand how the approved information was used. Revocation blocks future access through the grant; it cannot erase information already seen by a recipient.

### Scene 11 · 06:45–07:10 — Close with implemented value

**On screen:** Student overview or officer overview.

- Return to Student overview or Officer overview. Keep the demo label visible.
- Finish on APAAR Workspace and **SIH26263**. Include any outro inside this slot, then end the video.
- This wording works for local recording or a tested hosted deployment; it makes no unverified deployment or official-integration claim.

**Voice-over — read this:**

> Built with a Python FastAPI backend, PostgreSQL, and React, APAAR Workspace connects admission validation, correction, oversight, and student-controlled verification. Our aim is better institutional records, accountable review, and clear control over sharing. This is our prototype response to SIH problem statement SIH26263.

## 7. Existing-data alternatives

**College A already approved:** show Institution approval and its decision history. Read this instead of scene 2; do not claim a fresh refusal or first approval:

> This institution already has an officer-reviewed demo approval. Its history records the reviewer and the synthetic institution, year, programme intake, and validity evidence. Admission submissions are enabled only while that evidence remains applicable. Colleges cannot approve themselves. This is a simulated approval control, not actual AICTE verification.

**STU-080 already corrected:** open its resolved case/history, the retained original report, and current overview. Read this instead of scene 5; do not claim a live count drop:

> This case originally contained an invalid start date. Its history shows the reviewed correction and the applied result. The admission was saved after the correction, while the original error report was retained. The current dashboard excludes that corrected row from held work. Staff can trace the submitted issue to the current record without erasing the original evidence.

These substitutions remain below the 5,000-character limit and shorten the primary narration. If the relevant evidence/case does not exist, use a separate fresh synthetic database for the primary sequence. Keeping earlier admissions is acceptable: new uploads of existing canonical records may produce updates or no changes. Speak the actual outcome and avoid claiming new inserts or exact totals that are not on screen.

## 8. Final recording checklist

- [ ] HUMAN: Checked the actual voice track and screen actions once; retimed the edit to the recorded pace.
- [ ] HUMAN: Kept narration at or below 5,000 characters after any personal edits; only narration paragraphs are spoken.
- [ ] HUMAN: Confirmed College B is prepared and College A's approval scene matches its real current state.
- [ ] HUMAN: Showed the synthetic evidence and registry labels; made no claim of official AICTE approval, live APAAR integration, automatic fraud detection, or tamper-proof storage.
- [ ] HUMAN: Showed an actual correction result or honestly used the existing-case alternative.
- [ ] HUMAN: Verified that only Programme is returned and the same link is refused after Stop sharing.
- [ ] HUMAN: Removed passwords, `.env`, unrelated tabs, notifications and private configuration from the footage.
- [ ] HUMAN: Reviewed the exported 1080p MP4 and kept it below 8:30 including title/outro.

Document validation checks the character cap, synchronized narration and cue order. It does not mean a narrated video has been recorded, timed or reviewed by a person. Existing application-test evidence remains in the [progress checklist](05-progress-checklist.md).
