---
type: Narration Sections
title: Detailed demo narration by recording chapter
description: Spoken text grouped into the same chapters and step order as the action-by-action recording guide.
tags: [apaar, demo, voiceover, recording]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-28T05:48:21Z"}
sources:
  - resource: 14-demo-video-script.md
---

# Demo narration by chapter

Use the [action-by-action guide](14-demo-video-script.md) while filming. Each paragraph below matches one numbered step; its first sentence is spoken before the action and its result sentence, when present, is spoken after the wait condition. The guide identifies the exact split. Headings and code fences are not spoken.

Copy one chapter at a time for a voice tool or audio pickup. Every chapter is below 5,000 characters; there is no overall character or duration limit for this detailed version. Record/align one chapter at a time and leave pauses for actual interface responses. The [plain full narration](demo-voiceover.txt) contains the same paragraphs in the same order.

## Chapter 01 — Introduce the workspace and the college's starting position

Steps 001–003 · College A · tab 1.

```text
This is APAAR Workspace, our prototype for Smart India Hackathon 2026, AICTE problem statement SIH26263. Missing IDs and incorrect records complicate admissions. We help colleges check and correct data, while students control record sharing. Let's see it in action using synthetic data and simulated checks.

I am starting as the administrator of Deccan Institute of Technology, our first demo college. This college has no saved admissions yet.

The college also needs an officer's approval before it can submit admissions. I will first show how that requirement is enforced.
```

## Chapter 02 — Show why an unreviewed college cannot upload

Steps 004–009 · College A · tab 1.

```text
I open Upload admissions to begin the college's submission.

I select the academic year twenty twenty-six to twenty-seven.

I choose our prepared intake sixty-five CSV file from the fixtures folder. This file contains synthetic admissions only.

I try to validate this file while the college is still waiting for approval. The request is blocked. No admissions have been saved.

I open View approval to see what is missing.

The institution and programme evidence still need review. College staff cannot approve their own institution. I will switch to the officer account for that decision.
```

## Chapter 03 — Review and approve both synthetic institutions

Steps 010–022 · Officer · tab 2.

```text
I am now using the officer workspace, which can review institutions across both colleges.

I open Institution approval to review the colleges' evidence.

I select the same academic year as the college's submission.

For Deccan Institute, I check the synthetic institution identifier, campus, approval reference, validity dates, and programme intakes. These are simulated catalogue entries, not actual AICTE approval records.

I open Review demo evidence for this institution.

The dialog identifies the institution, year, source, and programmes that this decision will enable. Approval applies to this evidence and these programmes.

I acknowledge that I have reviewed the displayed synthetic evidence.

I approve demo access for Deccan Institute. Its matching programmes can now accept admission submissions.

I expand Evidence and decision history to check the recorded decision. The approval decision is recorded with its evidence.

I will also enable Riverdale Technical College, our second demo college, for a later cross-college example. No admission data has been imported for Riverdale yet.

I open Riverdale's evidence review and check its institution, academic year, validity and programme list.

I acknowledge the Riverdale evidence separately.

I approve demo access for Riverdale. Both colleges are now enabled, but their admissions remain separate.
```

## Chapter 04 — Return to College A and validate its admission file

Steps 023–035 · College A · tab 1.

```text
I return to the Deccan Institute administrator to continue the blocked submission.

I refresh the college's approval status. The college can now submit records for these matching programmes.

Before uploading, I open Programmes to check the configured courses and intake.

Computer Science is configured for this year with an intake of sixty. That is the demo comparison limit used in the report.

I return to Upload admissions.

I keep the upload in the same academic year.

I select the intake sixty-five CSV again for the actual validation.

I select Validate and preview to check the file without committing admissions.

The report contains sixty-five rows: sixty without issues, five warnings, and zero blocking errors. These are the results for this uploaded file.

I filter the report to the missing APAAR identifiers. These rows have identity gaps, but they are not structurally blocked admissions.

I open Why this issue to understand the warning and the next action. The guidance explains what staff should review. Its source is a synthetic demo rule.

I close the explanation and return to the file review.

I scroll to the intake preview before saving anything. The preview shows the proposed effect. These admissions have not been committed yet.
```

## Chapter 05 — Commit College A's acceptable rows and explain the dashboard

Steps 036–043 · College A · tab 1.

```text
I choose Save acceptable rows and hold errors, so structural problems stay outside the saved admissions.

I select Commit batch to save the reviewed submission.

I confirm that the batch should be committed to this institution. The sixty-five admissions are now saved.

I return to the overview to check the saved result.

The dashboard now shows sixty-five active admissions, sixty simulated identity matches, and five identity gaps. Missing identifiers remain visible and still count toward recorded intake.

Computer Science has sixty-five active admissions against the configured limit of sixty. This is a demo intake comparison, not an official regulatory finding.

I open the category breakdown to see the retained admission flags. Seat grouping and nationality flags are separate dimensions; adding every column would overcount students.

I close the breakdown so we can focus on correcting a blocked admission next.
```

## Chapter 06 — Stage a file with structural errors

Steps 044–056 · College A · tab 1.

```text
I open a second submission to demonstrate a structural error.

I select the same academic year for this correction example.

I choose the structural errors CSV, which contains three deliberately invalid synthetic rows.

I validate the second file before saving it.

This file has three rows and three blocking errors. These rows need correction before they can become admissions.

I keep the mode that saves acceptable rows and holds structural errors. In this file every row is blocked, so no new admission will be created by this commit.

I commit the reviewed batch so its blocked rows remain tracked as held work.

I confirm the commit. The existing sixty-five admissions have not increased.

I return to the overview to inspect the held work before correcting it.

There are two held admission candidates and one unassignable submitted row. The unknown programme cannot yet be assigned to a known admission target.

I reopen the structural errors submission to work on one specific candidate.

I filter the report to the invalid date. This candidate has an invalid start date.

I open a correction case for this specific issue. The Resolution Desk links this submitted issue to its next action and outcome.
```

## Chapter 07 — Preview, apply and verify the correction

Steps 057–064 · College A · tab 1.

```text
I select Review a correction to edit the affected admission data.

I replace the invalid start date with the fifteenth of July, twenty twenty-six, using year-month-day format.

I preview the correction before applying it.

The comparison shows the invalid value changing to the valid date. The preview explains the effect before the admission is saved.

I apply the reviewed correction. The save succeeds, and the case records the correction outcome.

I check the case history after the correction. The submitted issue and its resolution are traceable.

I return to the overview to check the admission and held-work counts.

Active admissions have increased to sixty-six. Held admission candidates have fallen from two to one. The corrected candidate is no longer counted as unresolved held work.
```

## Chapter 08 — Show the retained report and the saved enrolment

Steps 065–071 · College A · tab 1.

```text
I reopen the original submission to check what remains in its history.

I return to the original invalid-date row. The report still describes the original upload. It has not been rewritten to pretend the error never existed.

The original blocking-error summary is historical. Current held-work counts come from unresolved work, which is why the dashboard count fell.

I open Enrolments to confirm the corrected candidate is now a saved record.

I search for student reference eighty.

I open the saved enrolment. The student now has a canonical admission record. The earlier blocked input remains in the correction case.

I close the record details. Next I will introduce the second college's data so we can see how an overlap arises.
```

## Chapter 09 — Import the second college's records on screen

Steps 072–082 · College B · tab 3.

```text
I am now the administrator of Riverdale Technical College, our second demo institution.

Riverdale was approved earlier, but it has not imported admissions yet. This is a separate institution account and dataset.

I open Riverdale's Upload admissions page.

I select the same academic year.

I select the identity cases CSV for Riverdale. One verified synthetic student in this file is also enrolled at Deccan Institute.

I validate Riverdale's file.

The file has six rows: one without issues, five identity warnings, and no structural blocking errors. The warnings remain visible for follow-up.

I keep the mode that accepts structurally valid rows while retaining their identity warnings.

I commit Riverdale's reviewed submission.

I confirm the Riverdale commit. These are Riverdale's admissions, separate from Deccan's sixty-six records.

I return to Riverdale's overview. Both colleges have now submitted the shared student's enrolment. I will switch to the officer to review the date overlap.
```

## Chapter 10 — Review the overlap as an officer

Steps 083–092 · Officer · tab 2.

```text
I return to the officer workspace to inspect the combined result.

I open Admission oversight.

I refresh the overview after both colleges' commits. The officer can now see both institutions' recorded admissions.

There are two colleges, seventy-two active admissions, and one overlap awaiting review. Seventy-two counts enrolments, not seventy-two distinct people.

I open the overlap review queue.

The review brings together the two enrolments linked to the same simulated verified identity. This overlap needs investigation. It does not by itself prove fraud or an invalid admission.

I open the decision form after comparing the evidence.

I select More evidence needed because the date intersection alone does not settle the case.

I save that review outcome. Both admission records remain unchanged.

I filter to More evidence needed to find the recorded decision. The item remains available for follow-up rather than being treated as an automatic rejection.
```

## Chapter 11 — Inspect activity and check its integrity

Steps 093–097 · Officer · tab 2.

```text
I open Activity history to inspect the actions recorded during this workflow.

The history records actions such as batch commits, corrections, approvals and review decisions. This gives staff a way to investigate who changed what.

I run the integrity check on the retained audit history.

The check has passed for the retained events shown here. This checks the stored chain; it does not make the whole database tamper-proof.

I open the check's details and limits. The interface explains what the check can establish and where its limits remain.
```

## Chapter 12 — Open the student's records and personal card

Steps 098–106 · Student · tab 4.

```text
I am now signed in as synthetic student one, the student whose records were submitted by both colleges.

I refresh the student's view after the college submissions.

I open My records to choose the record to share. Each college's enrolment is shown separately.

I open the student card for the Deccan record.

The card summarises this enrolment and the student's workspace account. It is a personal record summary, not an official APAAR identity document or certificate.

I close the card and return to the same Deccan record.

I start sharing this specific Deccan record. Creating the code does not reveal the academic record.

I copy the one-use request code for the verifier. The verifier can use this code to ask for permission. It expires after fifteen minutes.

I close the dialog while keeping the request code in the clipboard. I will now act as the verifier who received that code.
```

## Chapter 13 — Submit a specific request as the verifier

Steps 107–114 · Verifier · tab 5.

```text
I am now using the approved demo verifier's account.

I open Request access to ask for specific information.

I paste the student's request code into the labelled field.

I choose Admission confirmation as the reason for the request.

I request the programme field.

I also request the institution field.

I send these two field requests to the student. This submits a permission request. It does not disclose either record value.

I open the request history to check the submission. The verifier still cannot see the student's unapproved record values.
```

## Chapter 14 — Approve fewer fields as the student

Steps 115–123 · Student · tab 4.

```text
I return to the student account to review that request.

I open Requests.

I refresh the inbox to load the verifier's new request.

The student can see the demo admissions verifier, its admission-confirmation purpose, and the Deccan record it wants to check. It asks for Programme and Institution, but neither field is preselected for approval.

I approve Programme only and leave Institution unchecked. The student can approve less than the verifier requested.

I set the sharing period to fifteen minutes. This is a time-limited grant, and the student can stop it earlier.

I approve the selected field for this verifier. The app opens Shared access and displays the new sharing card.

The card identifies the intended verifier, the one approved field, and the expiry. The QR and link represent the same limited permission; they do not publish the complete record.

I copy the consent link for the intended verifier. I will keep this same link for the verification and revocation checks.
```

## Chapter 15 — Open only the approved field as the verifier

Steps 124–128 · Verifier · tab 5.

```text
I return to the same verifier account that requested access.

I open Verify a link.

I paste the student's approved link into the labelled field.

I select Verify approved fields to check the current permission and open its allowed data.

The result contains Computer Science as the programme. The institution name is absent because the student did not approve it, even though the verifier originally requested it.
```

## Chapter 16 — Stop sharing and prove the same link is refused

Steps 129–139 · Student → Verifier → Student.

```text
I return to the student to stop this sharing grant.

I select Stop sharing on this verifier's grant.

I confirm that future checks through this grant should stop. The stop-sharing decision has been saved.

I return to the verifier to test the same link again. Stopping future access cannot erase information that was already viewed.

I clear the earlier result before making another request.

I paste the exact same link used in the successful check.

I try to verify through that link again after revocation. This new attempt is refused. The earlier permission no longer allows another check.

I return to the student to inspect the access record.

I open Access history.

I refresh the recorded accesses.

The history shows which verifier opened the approved field, for what purpose, and when. This gives the student visibility into the successful access. The revoked grant still cannot be used again.
```

## Chapter 17 — Close the story

Steps 140–141 · Student · tab 4.

```text
I return to the student overview to close the demonstration.

We have followed the complete path: institution approval, admission validation, correction, officer review, and student-controlled verification. APAAR Workspace uses Python, FastAPI, PostgreSQL, and React to connect these tasks in one workflow. This is our synthetic prototype for SIH26263; official AICTE and APAAR integration remain future work.
```
