import base64
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from conftest import TEST_PASSWORD, commit, login, upload
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit_integrity
from app.db import utcnow
from app.models import (
    Audit,
    ConsentGrant,
    Enrolment,
    RecordRequestHandle,
    User,
    VerificationAccess,
    VerificationRequest,
    VerifierOrganisation,
)
from app.security import Crypto
from app.seed import seed_verification


@pytest.fixture()
def actors(client, headers, fixtures_path):
    client.app.state.settings.consent_enabled = True
    with Session(client.app.state.engine) as db:
        db.info["audit_settings"] = client.app.state.settings
        seed_verification(db, TEST_PASSWORD, Crypto(client.app.state.settings))
    batch = upload(client, headers, fixtures_path, "intake-65.csv").json()
    assert commit(client, headers, batch["id"]).status_code == 200
    return {
        role: login(client, role + "@example.test")
        for role in ("student1", "student2", "verifier1", "verifier2")
    }


def request_consent(client, actors, *, key=None, requested=None):
    record = client.get("/api/v1/me/enrolments", headers=actors["student1"]).json()["items"][0]
    response = client.post(
        f"/api/v1/me/enrolments/{record['id']}/request-handles",
        headers=actors["student1"],
        json={"expected_version": record["version"]},
    )
    assert response.status_code == 201
    handle = response.json()["handle"]
    body = {
        "handle": handle,
        "purpose": "ADMISSION_CONFIRMATION",
        "requested_fields": requested or ["programme", "institution_name"],
    }
    response = client.post(
        "/api/v1/verification-requests",
        headers={**actors["verifier1"], "Idempotency-Key": key or str(uuid4())},
        json=body,
    )
    assert response.status_code == 202
    return response.json()["request_id"], body, record


def approve(client, actors, request_id, **kwargs):
    return client.post(
        f"/api/v1/me/verification-requests/{request_id}/approve",
        headers=actors["student1"],
        json={"expected_version": 1, "expected_record_version": 1, "allowed_fields": ["programme"], **kwargs},
    )


def resolve(client, actors, token, actor="verifier1"):
    return client.post("/api/v1/verification/resolve", headers=actors[actor], json={"token": token})


def test_student_scopes_explicit_consent_and_audited_field_only_disclosure(client, actors, caplog):
    assert client.get("/api/v1/me/enrolments", headers=actors["student1"]).json()["total"] == 1
    req, body, record = request_consent(client, actors)
    assert client.get("/api/v1/me/verification-requests", headers=actors["student2"]).json()["total"] == 0
    inbox = client.get("/api/v1/me/verification-requests", headers=actors["student1"]).json()["items"][0]
    assert inbox["verifier_organisation"] == "Demo admissions verifier"
    result = approve(client, actors, req)
    assert result.status_code == 200
    value = result.json()
    raw = value["token"]
    disclosed = resolve(client, actors, raw)
    assert disclosed.status_code == 200 and disclosed.json()["fields"] == {"programme": "Computer Science"}
    assert disclosed.headers["cache-control"] == "no-store"
    assert disclosed.headers["referrer-policy"] == "no-referrer"
    accesses = client.get("/api/v1/me/verification-accesses", headers=actors["student1"]).json()["items"]
    assert len(accesses) == 1 and accesses[0]["disclosed_fields"] == ["programme"]
    assert client.get("/api/v1/me/verification-accesses", headers=actors["student2"]).json()["total"] == 0
    repeated = approve(client, actors, req)
    assert (
        repeated.status_code == 200 and "token" not in repeated.json() and not repeated.json()["newly_issued"]
    )
    with Session(client.app.state.engine) as db:
        grant = db.get(ConsentGrant, value["grant"]["id"])
        assert grant.token_digest != raw and len(grant.token_digest) == 64
        assert db.scalar(select(func.count()).select_from(ConsentGrant)) == 1
        assert not any(
            raw in str(e.details) or body["handle"] in str(e.details) for e in db.scalars(select(Audit))
        )
        assert db.scalar(select(RecordRequestHandle.token_digest)) != body["handle"]
    assert raw not in caplog.text and body["handle"] not in caplog.text


def test_real_new_roles_denied_core_routes(client, actors, headers):
    from test_extension_permissions import route_requests

    programme = client.get("/api/v1/programmes", headers=headers).json()[0]
    record = client.get("/api/v1/enrolments", headers=headers).json()["items"][0]
    for actor in actors.values():
        assert client.get("/api/v1/auth/me", headers=actor).status_code == 200
        for method, path, options in route_requests(str(uuid4()), programme["id"], record["id"], b"bad"):
            if path == "/auth/me":
                continue
            assert (
                client.request(
                    method, "/api/v1" + path, headers={**actor, "Idempotency-Key": "denied"}, **options
                ).status_code
                == 403
            ), (method, path)
        for path in ("/resolution-cases", "/overlap-reviews", "/audit-events/verify"):
            assert client.get("/api/v1" + path, headers=actor).status_code == 403


def test_other_students_and_verifiers_cannot_act_on_grants(client, actors):
    req, body, record = request_consent(client, actors)
    assert (
        client.post(
            f"/api/v1/me/enrolments/{record['id']}/request-handles",
            headers=actors["student2"],
            json={"expected_version": 1},
        ).status_code
        == 404
    )
    for action, payload in [("approve", {"allowed_fields": ["programme"]}), ("deny", {})]:
        assert (
            client.post(
                f"/api/v1/me/verification-requests/{req}/{action}",
                headers=actors["student2"],
                json={"expected_version": 1, "expected_record_version": 1, **payload}
                if action == "approve"
                else {"expected_version": 1},
            ).status_code
            == 404
        )
    value = approve(client, actors, req).json()
    for action in ("revoke", "reissue"):
        assert (
            client.post(
                f"/api/v1/me/consent-grants/{value['grant']['id']}/{action}",
                headers=actors["student2"],
                json={"expected_version": 1},
            ).status_code
            == 404
        )
    assert resolve(client, actors, value["token"], "verifier2").status_code == 404
    assert resolve(client, actors, value["token"], "student1").status_code == 403
    # Binding includes the individual verifier, even within the same approved org.
    with Session(client.app.state.engine) as db:
        first = db.scalar(select(User).where(User.email == "verifier1@example.test"))
        second = db.scalar(select(User).where(User.email == "verifier2@example.test"))
        second.verifier_org_id = first.verifier_org_id
        db.commit()
    assert resolve(client, actors, value["token"], "verifier2").status_code == 404


def test_field_escalation_and_bad_input_denied(client, actors):
    req, _, _ = request_consent(client, actors, requested=["programme"])
    for fields in (["masked_apaar"], ["student_name"], [], ["programme", "programme"]):
        assert approve(client, actors, req, allowed_fields=fields).status_code == 422
    assert approve(client, actors, req, expires_in_minutes=61).status_code == 422
    assert approve(client, actors, req).status_code == 200


@pytest.mark.parametrize("mode", ["expired", "revoked", "changed", "wrong_key", "key_id", "student_inactive"])
def test_unavailable_links_do_not_disclose(client, actors, mode):
    req, _, record = request_consent(client, actors)
    value = approve(client, actors, req).json()
    with Session(client.app.state.engine) as db:
        grant = db.get(ConsentGrant, value["grant"]["id"])
        if mode == "expired":
            grant.expires_at = utcnow() - timedelta(seconds=1)
        elif mode == "revoked":
            grant.revoked_at = utcnow()
        elif mode == "changed":
            db.get(Enrolment, record["id"]).version += 1
        elif mode == "student_inactive":
            db.scalar(select(User).where(User.email == "student1@example.test")).active = False
        elif mode == "key_id":
            grant.token_key_id = "retired-key"
        db.commit()
    if mode == "wrong_key":
        client.app.state.settings.grant_token_key = SecretStr(
            base64.b64encode(secrets.token_bytes(32)).decode()
        )
    response = resolve(client, actors, value["token"])
    guessed = resolve(client, actors, "guessed-invalid-value")
    assert response.status_code == guessed.status_code == 404 and response.json() == guessed.json()
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(VerificationAccess)) == 0


def test_reissue_permanently_invalidates_old_link_and_revoke_is_idempotent(client, actors):
    req, _, _ = request_consent(client, actors)
    first = approve(client, actors, req).json()
    replacement = client.post(
        f"/api/v1/me/consent-grants/{first['grant']['id']}/reissue",
        headers=actors["student1"],
        json={"expected_version": 1},
    )
    assert replacement.status_code == 200
    second = replacement.json()
    assert resolve(client, actors, first["token"]).status_code == 404
    assert resolve(client, actors, second["token"]).status_code == 200
    path = f"/api/v1/me/consent-grants/{second['grant']['id']}/revoke"
    for _ in range(2):
        assert client.post(path, headers=actors["student1"], json={"expected_version": 1}).status_code == 200
    assert resolve(client, actors, second["token"]).status_code == 404


def test_changed_record_cannot_reissue_without_new_consent(client, actors):
    req, _, record = request_consent(client, actors)
    value = approve(client, actors, req).json()
    with Session(client.app.state.engine) as db:
        db.get(Enrolment, record["id"]).version += 1
        db.commit()
    assert (
        client.post(
            f"/api/v1/me/consent-grants/{value['grant']['id']}/reissue",
            headers=actors["student1"],
            json={"expected_version": 1},
        ).status_code
        == 409
    )


def test_approval_checks_the_record_version_the_student_actually_reviewed(client, actors):
    req, _, record = request_consent(client, actors)
    with Session(client.app.state.engine) as db:
        db.get(Enrolment, record["id"]).version += 1
        db.commit()
    assert approve(client, actors, req).status_code == 409
    assert approve(client, actors, req, expected_record_version=2).status_code == 200


def test_expired_handles_do_not_deliver_requests_and_request_rate_is_bounded(client, actors):
    req, body, _ = request_consent(client, actors)
    with Session(client.app.state.engine) as db:
        handle = db.scalar(select(RecordRequestHandle))
        handle.consumed_at = None
        handle.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    for index in range(9):
        response = client.post(
            "/api/v1/verification-requests",
            headers={**actors["verifier1"], "Idempotency-Key": f"expired-{index}"},
            json=body,
        )
        assert response.status_code == 202
    assert client.get("/api/v1/me/verification-requests", headers=actors["student1"]).json()["total"] == 1
    assert (
        client.post(
            "/api/v1/verification-requests",
            headers={**actors["verifier1"], "Idempotency-Key": "rate-denied"},
            json=body,
        ).status_code
        == 429
    )


def test_invalid_and_used_handle_have_same_acknowledgement_shape_and_no_student_oracle(client, actors):
    req, body, _ = request_consent(client, actors, key="repeatable")
    for key, value in [("used", body["handle"]), ("invalid", "missing-code")]:
        response = client.post(
            "/api/v1/verification-requests",
            headers={**actors["verifier1"], "Idempotency-Key": key},
            json={**body, "handle": value},
        )
        assert response.status_code == 202 and set(response.json()) == {"request_id", "status"}
    assert client.get("/api/v1/me/verification-requests", headers=actors["student1"]).json()["total"] == 1
    submissions = client.get(
        "/api/v1/me/verification-requests/submitted", headers=actors["verifier1"]
    ).json()["items"]
    assert len(submissions) == 3 and all(
        set(v) == {"id", "status", "version", "purpose", "requested_fields", "created_at", "expires_at"}
        for v in submissions
    )
    repeated = client.post(
        "/api/v1/verification-requests",
        headers={**actors["verifier1"], "Idempotency-Key": "repeatable"},
        json=body,
    )
    assert repeated.status_code == 202 and repeated.json()["request_id"] == req
    assert (
        client.post(
            "/api/v1/verification-requests",
            headers={**actors["verifier1"], "Idempotency-Key": "repeatable"},
            json={**body, "purpose": "EMPLOYMENT_CHECK"},
        ).status_code
        == 409
    )


def test_denied_and_expired_requests_cannot_approve(client, actors):
    req, _, _ = request_consent(client, actors)
    path = f"/api/v1/me/verification-requests/{req}/deny"
    assert client.post(path, headers=actors["student1"], json={"expected_version": 1}).status_code == 200
    assert approve(client, actors, req).status_code == 409
    expired, _, _ = request_consent(client, actors)
    with Session(client.app.state.engine) as db:
        db.get(VerificationRequest, expired).expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert approve(client, actors, expired).status_code == 409


def test_disabled_and_unapproved_verifier_cannot_authenticate_or_use_feature(client, actors, headers):
    with Session(client.app.state.engine) as db:
        org = db.scalar(
            select(VerifierOrganisation).where(VerifierOrganisation.reference == "DEMO-VERIFIER-1")
        )
        org.approved = False
        db.commit()
    assert client.get("/api/v1/auth/me", headers=actors["verifier1"]).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "verifier1@example.test", "password": TEST_PASSWORD}
        ).status_code
        == 401
    )
    client.app.state.settings.consent_enabled = False
    assert client.get("/api/v1/me/enrolments", headers=actors["student1"]).status_code == 401
    assert client.get("/api/v1/me/enrolments", headers=headers).status_code == 404


def test_disclosure_fails_closed_when_access_audit_fails(client, actors, monkeypatch):
    req, _, _ = request_consent(client, actors)
    value = approve(client, actors, req).json()

    def fail(*args):
        raise RuntimeError("Synthetic audit failure")

    monkeypatch.setattr(audit_integrity, "signed_hash", fail)
    response = resolve(client, actors, value["token"])
    assert response.status_code == 500 and "Computer Science" not in response.text
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(VerificationAccess)) == 0


def test_concurrent_approval_creates_one_grant_and_concurrent_revocation_stays_revoked(client, actors):
    req, _, _ = request_consent(client, actors)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: approve(client, actors, req), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert sum(r.json()["newly_issued"] for r in results) == 1
    value = next(r.json() for r in results if r.json()["newly_issued"])

    def revoke():
        return client.post(
            f"/api/v1/me/consent-grants/{value['grant']['id']}/revoke",
            headers=actors["student1"],
            json={"expected_version": 1},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        revoking = pool.submit(revoke)
        resolving = pool.submit(resolve, client, actors, value["token"])
        assert revoking.result(timeout=10).status_code == 200
        assert resolving.result(timeout=10).status_code in (200, 404)
    assert resolve(client, actors, value["token"]).status_code == 404
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(ConsentGrant)) == 1


def test_extension_seed_is_repeatable_without_password_or_binding_changes(client, actors):
    with Session(client.app.state.engine) as db:
        before = {
            u.email: (u.password_hash, u.person_id, u.verifier_org_id) for u in db.scalars(select(User))
        }
        db.info["audit_settings"] = client.app.state.settings
        seed_verification(db, "Different-password-is-never-applied", Crypto(client.app.state.settings))
        after = {u.email: (u.password_hash, u.person_id, u.verifier_org_id) for u in db.scalars(select(User))}
    assert before == after and len(after) == 7
