---
type: Demo Recording Script
title: Screen recording and voice-over script
description: A timed seven-minute-twenty-second platform demo with exact narration and screen actions.
tags: [apaar, demo, recording, voiceover, sih]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-27T18:26:07Z"}
sources:
  - resource: 12-demo-walkthrough.md
  - resource: 13-demo-interface.md
  - resource: 05-progress-checklist.md
---

# 14 — Demo video: screen actions and voice-over

**Planned runtime: 7 minutes 20 seconds.** Aim for a finished video around 6:30–7:30. Keep an **8:30 hard stop**, comfortably below the requested 8–9 minute maximum. Timing is an estimate, not a measured human rehearsal. Read only the voice-over paragraphs; the preparation and screen cues are not spoken. [The narration-only text](demo-voiceover.txt) is ready for a teleprompter or a second screen.

The main narration contains approximately **619 words**. At 115–130 words/minute it takes about 4.8–5.4 minutes to speak; the running order leaves the remaining time for actions and brief pauses. Speak and click together rather than adding every action after its paragraph.

## Before recording — outside the video

1. Pull the latest code and restart both servers. Confirm healthy API/database, simulated registry, both extension flags enabled, and normal mock operation (`MOCK_REGISTRY_OUTAGE=false`). Use the [Windows walkthrough](12-demo-walkthrough.md) and [current UI guide](13-demo-interface.md). Do not show terminals, passwords, `.env`, or secret configuration in the recording.
2. Use synthetic data only. A separate fresh, seeded demo database gives repeatable counts; do not delete/reset your existing database. The primary script expects College A to have no earlier copy of these demonstration records. If you keep existing records, check the actual totals and use the alternate correction scene below if STU-080 is already repaired.
3. Before filming, sign in as `collegeb@example.test`, upload and commit `fixtures/identity-cases.csv` for `2026-27`, and sign out. This prepares the second college's record so the officer's overlap appears when College A commits its matching record. Loading this fixture is preparation, not a live registry check.
4. Open a clean browser window with four tabs in this order: **College A** (`collegea@example.test`), **Officer** (`officer@example.test`), **Student** (`student1@example.test`), **Verifier** (`verifier1@example.test`). Sign in before recording. These sessions stay in each tab's memory. Switch with Ctrl+1 through Ctrl+4. **Do not reload the tabs**; reload requires sign-in. Sign in shortly before recording; sessions expire after one hour.
5. Have `fixtures/intake-65.csv` and `fixtures/structural-errors.csv` easy to select. The intended first file has **65 rows / 60 without issues / 5 warnings / 0 blocking errors**. A clean College A has 65 active admissions against basic intake 60 after the first commit; the script avoids speaking those dashboard totals so it can be adapted to existing data. The second file has **3 held rows**, comprising **2 held candidates + 1 unassignable row**. Repairing STU-080 makes the held-candidate count **2 → 1**, and creates one admission on that clean dataset.
6. Confirm audit integrity works. On the clean recording dataset, the overlap will appear **after College A commits in scene 3**, because College B was prepared earlier; do not pre-commit College A just to populate the queue. For an existing dataset with both colleges already committed, use the documented explicit interval backfill before recording if needed. Do not practise by applying the final correction to the only unresolved example you intend to film; use an isolated rehearsal dataset or the alternate scene.
7. Record the browser window at 1080p. Choose a readable browser zoom and test that labels and sign-out fit. Keep unrelated tabs and notifications out of view. Use a second screen or phone for this script. Pasting the code/link into the labelled fields avoids showing an opaque token in the address bar. Show only the synthetic QR; revoke its grant in the final scene. Never publish the demo password alongside the video.
8. Rehearse once with a stopwatch. Make cursor movements while speaking, pause only for the meaningful before/after states, and cut file-picker delays or long tab switches. Do not speed up the spoken narration to cover a stalled request. If behind schedule, omit opening the rule-help dialog and the audit-detail drawer; finish with the selective disclosure and stopped-access result. Do not add extra features after the closing paragraph.

## Running order

| Time | Scene | Main tab |
|---|---|---|
| 00:00–00:35 | The problem and our scope | College A overview |
| 00:35–01:20 | Upload and understand the file | College A → Upload admissions |
| 01:20–02:00 | Save records and keep honest counts | College A → Commit batch → Overview |
| 02:00–03:10 | Correct a held row with a reviewed change | College A → Upload admissions → Resolution Desk |
| 03:10–03:55 | Review an overlap without automatic rejection | Officer tab → Refresh overview → Overlap reviews |
| 03:55–04:20 | Check the activity history | Officer → Activity history |
| 04:20–05:00 | Show the student card and start sharing | Student tab → Refresh → My records |
| 05:00–06:25 | Prove that only approved fields are disclosed | Verifier → Student → Verifier |
| 06:25–07:00 | Stop sharing and inspect access history | Student → Verifier → Student |
| 07:00–07:20 | Close with the implemented value | Student overview or officer overview |

## 1. 00:00–00:35 — The problem and our scope

**On screen:** College A overview.

- Start on the college overview. Keep the simulated-registry/demo label visible.
- Move the pointer once across the admissions and data-quality areas; avoid reading every number.

**Voice-over — read this:**

> A student record can fail a check because of a missing identifier, a wrong date, or an outdated college entry. Staff then spend time comparing spreadsheets and deciding what to fix. APAAR Workspace brings that work into one controlled flow: review, correct, count, and share with permission. This demonstration uses synthetic student data and a simulated registry.

## 2. 00:35–01:20 — Upload and understand the file

**On screen:** College A → Upload admissions.

- Choose 2026-27 and fixtures/intake-65.csv. Select Validate and preview.
- Filter APAAR missing. Point to one explanation and its separate Open case button.
- Open Why this issue? briefly, then close the dialog. Do not open a missing-ID case in this scene.

**Voice-over — read this:**

> I am signed in as a college administrator. I choose the academic year and upload our sample CSV. The platform checks the file before changing any admissions. This example has sixty-five rows: sixty have no issues, five have identity warnings, and none have blocking errors. I can filter those warnings. Each row gives a readable explanation, a help link, and a separate action to open a correction case.

## 3. 01:20–02:00 — Save records and keep honest counts

**On screen:** College A → Commit batch → Overview.

- Keep Save acceptable rows; hold errors selected. Select Commit batch and accept the confirmation.
- Select Back to overview. Show Active admissions, Identity gaps, and the intake comparison.
- Expand the category breakdown briefly. Do not describe a nationality flag as proof of quota eligibility.

**Voice-over — read this:**

> Here is why the distinction matters. A missing identifier is an identity gap; it does not automatically remove a recorded admission from the intake count. I save the acceptable rows and return to the overview. The dashboard separates active admissions, unresolved identity details, intake warnings, and held candidates. The category breakdown keeps base and supernumerary counts separate from nationality flags.

## 4. 02:00–03:10 — Correct a held row with a reviewed change

**On screen:** College A → Upload admissions → Resolution Desk.

- Upload fixtures/structural-errors.csv and commit acceptable rows. Three rows remain held; the dashboard treats two as held candidates and one as unassignable.
- Open the DATE_INVALID case for STU-080. Select Review a correction.
- Set Start date to 2026-07-15. Select Preview correction, show the change and active-count effect, then Apply correction.
- Return to Overview and point to the held-candidate count: 2 → 1 on the rehearsed clean dataset.

**Voice-over — read this:**

> Now I upload a second file with an incorrect start date. The invalid row stays outside the saved admission records. I open its case and review a correction. I change the date, then preview the repair. This shows the field change and its effect on intake before I apply it. After I apply it, the valid record is saved, the case resolves, and the held-candidate count falls by one. The original error report remains available, so staff can see both the submitted problem and the later correction.

## 5. 03:10–03:55 — Review an overlap without automatic rejection

**On screen:** Officer tab → Refresh overview → Overlap reviews.

- Switch to the pre-signed-in officer tab and select Refresh overview.
- Open Overlap reviews → Review this overlap. Point to the two college records and overlapping dates.
- Choose More evidence needed under Review outcome and select Save review. Show the success message.

**Voice-over — read this:**

> The officer can now review a record reported by two colleges with overlapping dates. Both entries are shown together, so the officer can compare the evidence before recording an outcome. An overlap is a reason to investigate, not an automatic fraud finding. In this demo, I select More evidence needed. Both admission records remain available, and the decision is recorded for follow-up.

## 6. 03:55–04:20 — Check the activity history

**On screen:** Officer → Activity history.

- Open Activity history and select Run integrity check.
- Hold on the result. Leave Check details and limits collapsed unless the rehearsal is comfortably ahead of time.

**Voice-over — read this:**

> Next, I run the history integrity check. It checks retained audit entries against their stored chain. The result shows how many events were checked and their sequence. This helps identify changes to retained history; it does not make the database tamper-proof.

## 7. 04:20–05:00 — Show the student card and start sharing

**On screen:** Student tab → Refresh → My records.

- Choose the Deccan Institute of Technology record. Select View student card, show the masked number, then close it.
- Select Start sharing for that same record. Select Copy request code.
- Close the dialog after copying. Do not reload the student tab.

**Voice-over — read this:**

> The student has a simpler view. My records shows the records linked to this account. The student card summarises the course, college, academic year, admission state, and masked APAAR. It is a demo record summary. To share a record, the student starts sharing and copies a one-use request code. Creating this code does not disclose the record.

## 8. 05:00–06:25 — Prove that only approved fields are disclosed

**On screen:** Verifier → Student → Verifier.

- Verifier tab: Request access → paste code → Admission confirmation → select Programme and Institution → Send approval request.
- Student tab: Requests → Refresh → choose only Programme → Allow access for 5 minutes → Approve selected fields.
- The student is moved to Shared access. Briefly show the QR/card, recipient, approved field, and expiry. Select Copy consent link.
- Verifier tab: Verify a link → paste into Student consent link → Verify approved fields. Show that the result has Programme only. Keep this same link in the clipboard for the next scene.

**Voice-over — read this:**

> On the verifier tab, I paste that code, choose a purpose, and request Programme and Institution. The student opens Requests and refreshes the inbox. They see who is asking and why. Nothing is preselected. I approve only Programme, for five minutes. The platform moves to Shared access and displays the new QR and link. I copy that link and return to the verifier. When I open it, the result contains only the course name. The college name stays hidden because the student did not approve it. Access also depends on the signed-in verifier, expiry, and the current consent.

## 9. 06:25–07:00 — Stop sharing and inspect access history

**On screen:** Student → Verifier → Student.

- Student tab: Shared access → Stop sharing → Confirm stop sharing.
- Verifier tab: paste the same link again and select Verify approved fields. Show This link cannot be opened.
- Student tab: Access history → show the organisation, Programme field, and access time.

**Voice-over — read this:**

> The student can stop sharing at any time. I confirm Stop sharing, then try the same link again on the verifier tab. This time the check is refused. The student can also open Access history to see the organisation, approved field names, and access time. Stopping access prevents future checks; it cannot take back information already viewed.

## 10. 07:00–07:20 — Close with the implemented value

**On screen:** Student overview or officer overview.

- Return to a clean overview. Keep the demo label visible.
- End the recording; do not add installation steps, source-code browsing, or extra feature tours.

**Voice-over — read this:**

> Built with Python, FastAPI, PostgreSQL, and React, APAAR Workspace connects correction, honest admission counts, review, and controlled sharing in one workflow. This is a local prototype; official integration remains outside this demonstration.

## Alternate correction scene for an already-used dataset

If STU-080 is already resolved, **do not claim a new repair or a live count decrease**. Open its resolved case and correction history from the Resolution Desk, then show the retained original report and current overview. Replace scene 4's narration with:

> This case originally contained an invalid start date. Its history shows the reviewed correction and the applied result. The row was saved after the correction, while the original error report was retained. The dashboard now excludes that corrected row from held work. This gives staff a traceable path from the submitted problem to the current record, without erasing the original evidence.

This shorter alternative reduces the total runtime. If the relevant case/history does not exist, use the primary scene on a separate fresh synthetic dataset. Do not invent a before/after result.

## Delivery checklist

- [ ] HUMAN: Rehearsed once and checked actual data/counts against these cues.
- [ ] HUMAN: Captured readable UI and a clear voice track; no passwords or private configuration shown.
- [ ] HUMAN: Kept the finished video below 8:30, including any title/outro.
- [ ] HUMAN: Confirmed the approved result contains Programme only, and the same link is refused after stopping access.
- [ ] HUMAN: Used the local/simulated wording; did not claim live APAAR integration, official certification, automatic fraud detection, national deployment, or tamper-proof storage.

These boxes describe the user's recording/review work. Producing this script and passing browser checks do not mean a narrated video has been recorded or timed by a person.
