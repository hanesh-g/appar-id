"""Exercise approval gates against PostgreSQL and the actual role-scoped API."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Event

from conftest import TEST_PASSWORD, commit, login, upload
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from test_corrections import apply, propose
from test_resolution_cases import staged_case

from app import institution_approval, services
from app.errors import DomainError
from app.models import (
    Audit,
    Batch,
    Enrolment,
    Institution,
    InstitutionApproval,
    InstitutionApprovalEvent,
)
from app.security import Crypto
from app.seed import seed, seed_verification


def clear_approvals(client):
    with Session(client.app.state.engine) as db:
        db.execute(delete(InstitutionApprovalEvent))
        db.execute(delete(InstitutionApproval))
        db.commit()


def approvals(client, headers, year="2026-27"):
    response = client.get("/api/v1/institution-approvals", headers=headers, params={"academic_year": year})
    assert response.status_code == 200, response.text
    return response.json()


def decide(client, officer, entry, action="APPROVE_DEMO", **extra):
    return client.post(
        f"/api/v1/institution-approvals/{entry['institution_id']}/decisions",
        headers=officer,
        json={
            "academic_year": entry["academic_year"],
            "expected_version": entry["version"],
            "evidence_digest": entry["evidence_digest"],
            "action": action,
            **extra,
        },
    )


def test_pending_gate_keeps_reads_and_seed_does_not_grant_approval(client, headers, fixtures_path):
    clear_approvals(client)
    with Session(client.app.state.engine) as db:
        seed(db, TEST_PASSWORD)
        assert db.scalar(select(func.count()).select_from(InstitutionApproval)) == 0
    own = approvals(client, headers)
    assert len(own) == 1 and own[0]["status"] == "PENDING"
    assert own[0]["version"] == 0 and own[0]["can_approve"]
    denied = upload(client, headers, fixtures_path)
    assert denied.status_code == 403 and denied.json()["code"] == "INSTITUTION_APPROVAL_REQUIRED"
    assert client.get("/api/v1/enrolments", headers=headers).status_code == 200
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Batch)) == 0


def test_officer_review_enables_only_the_reviewed_institution_and_records_evidence(
    client, headers, fixtures_path
):
    clear_approvals(client)
    officer = login(client, "officer@example.test")
    own = approvals(client, headers)[0]
    assert decide(client, headers, own).status_code == 403
    result = decide(client, officer, own)
    assert result.status_code == 200, result.text
    reviewed = result.json()
    assert reviewed["status"] == "APPROVED" and reviewed["version"] == 1
    assert reviewed["reviewer"] == "Demo officer"
    assert reviewed["reviewed_evidence"]["mode"] == "DEMO_FIXTURE"
    assert reviewed["reviewed_evidence"]["aicte_id"].startswith("DEMO-")
    assert all(p["admissions_enabled"] for p in reviewed["programmes"])
    assert len(reviewed["events"]) == 1
    assert upload(client, headers, fixtures_path).status_code == 201
    other = login(client, "collegeb@example.test")
    assert upload(client, other, fixtures_path, key="other").status_code == 403
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(InstitutionApprovalEvent)) == 1
        event = db.scalar(select(Audit).where(Audit.action == "INSTITUTION_APPROVAL_REVIEWED"))
        assert event.details["mode"] == "DEMO_FIXTURE" and event.sequence_no >= 1


def test_student_and_verifier_cannot_read_or_decide_approval(client, headers):
    officer = login(client, "officer@example.test")
    entry = approvals(client, officer)[0]
    client.app.state.settings.consent_enabled = True
    with Session(client.app.state.engine) as db:
        db.info["audit_settings"] = client.app.state.settings
        seed_verification(db, TEST_PASSWORD, Crypto(client.app.state.settings))
    for account in ("student1@example.test", "verifier1@example.test"):
        actor = login(client, account)
        assert client.get("/api/v1/institution-approvals", headers=actor).status_code == 403
        assert decide(client, actor, entry).status_code == 403
    assert client.get("/api/v1/institution-approvals").status_code == 401


def test_unknown_source_and_academic_year_cannot_be_approved(client, headers, fixtures_path):
    clear_approvals(client)
    officer = login(client, "officer@example.test")
    future = approvals(client, headers, "2027-28")[0]
    assert not future["can_approve"] and future["candidate_evidence"] is None
    assert decide(client, officer, future).status_code == 409
    with Session(client.app.state.engine) as db:
        db.get(Institution, future["institution_id"]).reference = "UNKNOWN-COLLEGE"
        db.commit()
    unknown = approvals(client, headers)[0]
    assert unknown["status"] == "PENDING" and unknown["candidate_evidence"] is None
    assert decide(client, officer, unknown).status_code == 409
    assert upload(client, headers, fixtures_path).status_code == 403
    assert (
        client.get("/api/v1/institution-approvals?academic_year=2026-28", headers=headers).status_code == 422
    )


def test_expired_evidence_blocks_upload_and_cannot_be_renewed(client, headers, fixtures_path, monkeypatch):
    monkeypatch.setattr(services, "business_date", lambda: date(2027, 7, 1))
    own = approvals(client, headers)[0]
    assert own["status"] == "EXPIRED" and not own["can_approve"]
    assert not any(p["admissions_enabled"] for p in own["programmes"])
    assert upload(client, headers, fixtures_path).status_code == 403
    assert decide(client, login(client, "officer@example.test"), own).status_code == 409


def test_intake_changes_block_affected_programme_until_matching_evidence_reviewed(
    client, headers, fixtures_path
):
    officer = login(client, "officer@example.test")
    programme = next(
        p for p in client.get("/api/v1/programmes", headers=headers).json() if p["name"] == "Computer Science"
    )
    old_review = approvals(client, headers)[0]
    path = f"/api/v1/programmes/{programme['id']}"
    assert client.patch(path, headers=headers, json={"approved_intake": 61}).status_code == 200
    result = upload(client, headers, fixtures_path)
    assert result.status_code == 403 and result.json()["code"] == "PROGRAMME_APPROVAL_REQUIRED"
    assert decide(client, officer, old_review).status_code == 409
    changed = approvals(client, headers)[0]
    assert len([p for p in changed["programmes"] if p["admissions_enabled"]]) == 1
    assert decide(client, officer, changed, evidence_snapshot={"intake": 61}).status_code == 422
    # Reviewing the remaining matching programme cannot approve the altered intake.
    assert decide(client, officer, changed).status_code == 200
    assert upload(client, headers, fixtures_path).status_code == 403
    assert client.patch(path, headers=headers, json={"approved_intake": 60}).status_code == 200
    assert upload(client, headers, fixtures_path).status_code == 403  # latest snapshot omitted CS
    assert decide(client, officer, approvals(client, headers)[0]).status_code == 200
    assert upload(client, headers, fixtures_path).status_code == 201


def test_new_programme_cannot_use_college_approval_as_its_own_evidence(client, headers, fixtures_path):
    created = client.post(
        "/api/v1/programmes",
        headers=headers,
        json={"name": "Mechanical Engineering", "academic_year": "2026-27", "approved_intake": 60},
    )
    assert created.status_code == 201
    content = (
        (fixtures_path / "intake-65.csv").read_text().replace("Computer Science", "Mechanical Engineering")
    )
    response = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "new-programme"},
        data={"academic_year": "2026-27"},
        files={"file": ("new.csv", content, "text/csv")},
    )
    assert response.status_code == 403 and response.json()["code"] == "PROGRAMME_APPROVAL_REQUIRED"


def test_suspension_blocks_staged_commit_but_retains_existing_records(client, headers, fixtures_path):
    original = upload(client, headers, fixtures_path).json()
    assert commit(client, headers, original["id"]).status_code == 200
    pending = upload(client, headers, fixtures_path, key="pending").json()
    officer = login(client, "officer@example.test")
    assert decide(client, officer, approvals(client, headers)[0], "SUSPEND").status_code == 200
    blocked = commit(client, headers, pending["id"])
    assert blocked.status_code == 403 and blocked.json()["code"] == "INSTITUTION_APPROVAL_REQUIRED"
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 6
    assert client.get(f"/api/v1/batches/{original['id']}", headers=headers).status_code == 200
    # A completed operation is a read-only replay, not a new write.
    assert commit(client, headers, original["id"]).status_code == 200
    assert decide(client, officer, approvals(client, headers)[0]).status_code == 200
    assert commit(client, headers, pending["id"]).status_code == 200


def test_suspension_blocks_correction_apply_and_preview(client, headers, fixtures_path):
    _, _, case = staged_case(client, headers, fixtures_path)
    proposal = propose(client, headers, case)
    officer = login(client, "officer@example.test")
    assert decide(client, officer, approvals(client, headers)[0], "SUSPEND").status_code == 200
    assert apply(client, headers, proposal).status_code == 403
    response = client.post(
        f"/api/v1/resolution-cases/{case['id']}/correction-previews",
        headers=headers,
        json={"expected_version": case["version"], "changes": {"start_date": "2026-07-15"}},
    )
    assert response.status_code == 403
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        assert db.scalar(select(func.count()).select_from(Batch)) == 1


def test_suspension_blocks_identity_retry(client, headers, fixtures_path):
    client.app.state.settings.mock_registry_outage = True
    batch = upload(client, headers, fixtures_path).json()
    assert commit(client, headers, batch["id"]).status_code == 200
    client.app.state.settings.mock_registry_outage = False
    officer = login(client, "officer@example.test")
    assert decide(client, officer, approvals(client, headers)[0], "SUSPEND").status_code == 200
    result = client.post("/api/v1/enrolments/recheck-identities", headers=headers)
    assert result.status_code == 403


def test_approval_decision_rolls_back_when_audit_fails(client, headers, monkeypatch):
    clear_approvals(client)
    officer = login(client, "officer@example.test")
    own = approvals(client, headers)[0]

    def refused(*args, **kwargs):
        raise DomainError("AUDIT_UNAVAILABLE", "Audit unavailable", 503)

    monkeypatch.setattr(services, "audit", refused)
    assert decide(client, officer, own).status_code == 503
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(InstitutionApproval)) == 0
        assert db.scalar(select(func.count()).select_from(InstitutionApprovalEvent)) == 0


def test_concurrent_first_decisions_have_one_winner(client, headers):
    clear_approvals(client)
    officer = login(client, "officer@example.test")
    own = approvals(client, headers)[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: decide(client, officer, own).status_code, range(2)))
    assert sorted(results) == [200, 409]
    assert len(approvals(client, headers)[0]["events"]) == 1


def test_suspension_serialises_before_pending_commit(client, headers, fixtures_path, monkeypatch):
    batch = upload(client, headers, fixtures_path).json()
    officer = login(client, "officer@example.test")
    own = approvals(client, headers)[0]
    locked, release = Event(), Event()
    original_audit = services.audit

    def pause_before_commit(db, user, action, entity_id, details=None):
        if action == "INSTITUTION_APPROVAL_REVIEWED" and details["status"] == "SUSPENDED":
            locked.set()
            assert release.wait(10)
        return original_audit(db, user, action, entity_id, details)

    monkeypatch.setattr(services, "audit", pause_before_commit)
    with ThreadPoolExecutor(max_workers=2) as pool:
        suspension = pool.submit(decide, client, officer, own, "SUSPEND")
        assert locked.wait(10)
        saving = pool.submit(commit, client, headers, batch["id"])
        release.set()
        assert suspension.result(timeout=15).status_code == 200
        assert saving.result(timeout=15).status_code == 403
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 0


def test_missing_catalogue_fails_closed(client, headers, fixtures_path, monkeypatch, tmp_path):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(institution_approval, "CATALOGUE_PATH", missing)
    response = upload(client, headers, fixtures_path)
    assert response.status_code == 503 and response.json()["code"] == "APPROVAL_SOURCE_UNAVAILABLE"


def test_changed_source_requires_new_review(client, headers, fixtures_path, monkeypatch, tmp_path):
    original, _ = institution_approval.catalogue()
    original["version"] = "SYNTHETIC-APPROVAL-2026-v2"
    changed = tmp_path / "updated-source.json"
    changed.write_text(json.dumps(original))
    monkeypatch.setattr(institution_approval, "CATALOGUE_PATH", changed)
    own = approvals(client, headers)[0]
    assert own["status"] == "REVIEW_REQUIRED"
    assert own["reviewed_evidence"]["catalogue_version"] != own["candidate_evidence"]["catalogue_version"]
    assert upload(client, headers, fixtures_path).status_code == 403
    assert decide(client, login(client, "officer@example.test"), own).status_code == 200
    assert upload(client, headers, fixtures_path).status_code == 201
