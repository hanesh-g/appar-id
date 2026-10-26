---
type: Product Brief
title: Problem and scope
description: Define users, product value, demo boundaries, and honest admission counts.
tags: [apaar, scope, product, demo]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-26T16:12:00Z"}
sources:
  - resource: "User-uploaded APAAR ID Student Data Platform (SIH26263) Phase-by-Phase Build Guide.pdf, 18 pages"
  - resource: "User requirements in this conversation: Python backend, two-day demo, Vercel and Render"
---

# 01 — Problem and scope

## 1. The problem from first principles

An institution records who joins a programme. Other institutions keep separate records. A regulator needs to compare these records across institutions and academic years.

Local student numbers do not connect those records. Names can vary. Admission data can contain typing errors, repeated rows, missing identifiers, or old enrolments that were not closed after a transfer.

The result is uncertainty about identity, admission totals, and the reliability of a record supplied for verification. Manual spreadsheets make correction and change tracking difficult.

This platform provides a controlled path from institution-submitted data to reviewable student and enrolment records.

## 2. Product purpose

Help institutions submit better admission data. Help officers see gaps and possible intake problems. Provide a foundation for restricted, accountable verification of student records.

The proposed repository is an application database for the demo. It is **not an official AICTE repository**. APAAR checks use a simulated registry.

## 3. Essential concepts

| Term | Meaning |
|---|---|
| Person | A student's identity, separate from an individual admission. |
| Enrolment | That person's admission to a programme at an institution, with dates and a status. |
| APAAR ID | The cross-institution identifier assumed by this design. Its real API contract is unknown. |
| Approved intake | The programme's configured admission limit for a year. Demo values are synthetic. |
| Identity status | Whether the submitted identity matched the mock registry, needs review, is invalid, or is missing. |
| Dry run | A report that previews a batch before main enrolment records change. |
| Commit | An explicit operation that saves acceptable staged rows. |
| Held row | A submitted row that cannot be committed until a blocking data error is fixed. |
| Issue | A coded problem with a severity, explanation, field, and correction action. |

One person can have more than one enrolment over time. An overlapping enrolment is a reason to investigate, not automatic proof of fraud.

## 4. Users and their needs

| User | Need | Demo treatment |
|---|---|---|
| Institution administrator | Submit admissions, fix errors, inspect own records. | CORE; seed two institutions to test isolation. |
| AICTE-style officer | Compare intake and data quality; inspect permitted issues. | CORE; clearly a demo officer role. |
| Student | Understand and control record verification. | Optional E7 delivered locally; person-bound own records and consent. |
| Authorised verifier | Receive a narrowly permitted statement about a record. | Optional E7 delivered locally; approved recipient and live grants only. |
| Policy analyst | Use aggregate trends without unnecessary personal details. | LATER separate role; core officer charts use limited aggregates. |
| System administrator/auditor | Manage access and examine changes. | Seeded accounts and scoped officer history in CORE; separate consoles LATER. |

## 5. Core demonstration

1. An institution user logs in and sees only their institution.
2. The user selects a programme and year, then uploads a CSV.
3. The platform finds field errors and simulated identity problems.
4. The user reviews the dry run and downloads a correction report.
5. The user commits acceptable rows. Blocked rows remain visible.
6. A correction upload updates records without adding duplicates.
7. The officer sees intake, unresolved identities, held rows, and change history.
8. A simulated registry outage leaves identities pending. An explicit retry resolves eligible records after recovery.

If the core passes, add student-approved verification as the first extension. Do not claim the full upload-to-authorised-verification journey if that extension is absent.

## 6. Non-negotiable rules

- Authentication is required for student data. Backend object-level access checks are mandatory.
- Missing, invalid, and pending identity states do not make otherwise well-formed admissions disappear.
- Identity issues are warnings. Structural errors can block a row. This resolves an inconsistency in the source guide.
- Display committed admissions separately from held candidates and submitted-row totals.
- Do not add counts from repeated uploads. Count canonical enrolment keys and labelled candidates.
- The same batch cannot be committed twice. A correction updates the same enrolment key.
- Dry-run validation does not change main enrolments.
- An ID match does not prove that admission or course completion claims are true.
- A dashboard warning is an observation, not a legal finding.
- Synthetic data and visible mock labels are required for the demo.

## 7. Intake meaning for the demo

The core metric is **active recorded enrolments in a programme and academic year**, as of the application date. Include every identity state. Exclude withdrawn, transferred, and completed enrolments from this active metric.

Preview the effect of acceptable staged updates over the current database. Do not simply add the file's row count. Show held candidates separately when their programme and unique key can be resolved. Show unassignable rows as a separate total.

Example: approved intake is 60. A clean submission has 65 distinct active enrolments. Five have no APAAR ID. After commit, the active count is 65, the identity-gap count is 5, and the excess is 5.

If five rows have blocking errors instead, do not report them as confirmed enrolments. Show the committed count and five held candidates. Flag the incomplete intake picture.

Actual AICTE rules may treat quotas, supernumerary seats, and admission categories differently. The demo must not claim official compliance calculations. Retain those flags, label the basic calculation, and obtain the applicable policy before implementing exceptions.

## 8. Scope boundaries

CORE: F01–F11 in the feature specification.

Optional local extensions now include F12 consent-based verification, F13 synthetic overlap review, and deterministic rule help/category views. An LLM rules-help runtime remains unimplemented. Official policy review and hosted release remain separate gates.

LATER: F15 real registry/large-scale ingestion and F16 production governance. No real registry connection, public certificate claims, full college ERP, payment system, trained fraud model, blockchain, or automated regulatory decisions in the core.

## 9. Evidence of success

The chosen synthetic fixture produces the expected issue counts. Counts include unresolved identities. Cross-institution data access fails. Repeated upload/commit operations do not duplicate enrolments. Deployment survives a backend restart with data preserved. The selected demo journey passes in the deployed system.

An attractive dashboard alone does not meet these conditions.

## 10. Human confirmations

Before presentation, the team confirms the official SIH statement, which intake rule is being illustrated, the proposed core scope, and the final mock disclosures. Before any real-data pilot, authorised stakeholders must confirm registry access, legal basis, consent where required, retention, and operational responsibilities. These are separate from writing application code.
