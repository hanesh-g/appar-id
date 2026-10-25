import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import jwt
import pytest
from conftest import TEST_PASSWORD, commit, login, upload
from cryptography.exceptions import InvalidTag
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import services
from app.db import utcnow
from app.models import Audit, Enrolment, History, Institution, Person, User
from app.security import Crypto


def test_health_and_authentication(client):
    assert client.get("/api/v1/health").json()["database"] == "ok"
    assert client.get("/api/v1/enrolments").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "unknown@example.test", "password": "wrong"}
        ).status_code
        == 401
    )
    headers = login(client)
    data = client.get("/api/v1/auth/me", headers=headers).json()
    assert data["role"] == "institution_admin"
    assert "password_hash" not in data
    assert "token" not in data


def test_invalid_expired_and_inactive_tokens(client, headers):
    settings = client.app.state.settings
    me = client.get("/api/v1/auth/me", headers=headers).json()
    expired = jwt.encode(
        {
            "sub": me["id"],
            "iat": utcnow() - timedelta(hours=2),
            "exp": utcnow() - timedelta(hours=1),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + expired}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    with Session(client.app.state.engine) as db:
        db.get(User, me["id"]).active = False
        db.commit()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_login_rate_limit(client):
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "bad@example.test", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/api/v1/auth/login", json={"email": "bad@example.test", "password": "wrong"}).status_code
        == 429
    )


def test_programme_scope_and_validation(client, headers):
    other = login(client, "collegeb@example.test")
    foreign = client.get("/api/v1/programmes", headers=other).json()[0]
    assert (
        client.patch(
            f"/api/v1/programmes/{foreign['id']}", headers=headers, json={"approved_intake": 10}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/programmes",
            headers=headers,
            json={"name": "New", "academic_year": "2026-27", "approved_intake": -1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/programmes",
            headers=headers,
            json={"name": "New", "academic_year": "2026-28", "approved_intake": 10},
        ).status_code
        == 422
    )
    officer = login(client, "officer@example.test")
    assert (
        client.post(
            "/api/v1/programmes",
            headers=officer,
            json={"name": "New", "academic_year": "2026-27", "approved_intake": 10},
        ).status_code
        == 403
    )


def test_identity_fixture_and_dry_run(client, headers, fixtures_path):
    response = upload(client, headers, fixtures_path)
    assert response.status_code == 201, response.text
    summary = response.json()["summary"]
    assert summary["identity_counts"] == {"VERIFIED": 1, "MISSING": 1, "INVALID": 3, "PENDING_CHECK": 1}
    assert summary["rows_error"] == 0
    assert summary["rows_warning"] == 5
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 0
    rows = client.get(f"/api/v1/batches/{response.json()['id']}/rows", headers=headers).json()
    assert rows["total"] == 6
    assert "student_name" not in json.dumps(rows)


def test_counting_and_repeat_operations(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "intake-65.csv").json()
    assert batch["summary"]["intake"][0]["after"] in (0, 65)
    first = commit(client, headers, batch["id"])
    assert first.status_code == 200, first.text
    assert first.json()["result"] == {"created": 65, "updated": 0, "unchanged": 0, "held": 0}
    second = commit(client, headers, batch["id"])
    assert second.json() == first.json()
    repeated = upload(client, headers, fixtures_path, "intake-65.csv", "second-key").json()
    result = commit(client, headers, repeated["id"]).json()["result"]
    assert result == {"created": 0, "updated": 0, "unchanged": 65, "held": 0}
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["active"] == 65
    assert dashboard["identity_counts"]["MISSING"] == 5
    assert dashboard["excess"] == 5


def test_correction_updates_without_duplicates(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "intake-65.csv").json()
    assert commit(client, headers, batch["id"]).status_code == 200
    corrected = upload(client, headers, fixtures_path, "corrections.csv", "correction").json()
    result = commit(client, headers, corrected["id"]).json()["result"]
    assert result == {"created": 0, "updated": 1, "unchanged": 1, "held": 0}
    records = client.get("/api/v1/enrolments?search=STU-001", headers=headers).json()["items"]
    assert len(records) == 1 and records[0]["version"] == 2


def test_request_idempotency(client, headers, fixtures_path):
    first = upload(client, headers, fixtures_path).json()
    second = upload(client, headers, fixtures_path).json()
    assert first["id"] == second["id"]
    assert upload(client, headers, fixtures_path, "structural-errors.csv").status_code == 409


def test_errors_held_and_all_or_nothing(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "structural-errors.csv").json()
    assert batch["summary"]["rows_error"] == 3
    assert commit(client, headers, batch["id"], "all_or_nothing").status_code == 409
    result = commit(client, headers, batch["id"]).json()["result"]
    assert result["held"] == 3 and result["created"] == 0
    same = upload(client, headers, fixtures_path, "structural-errors.csv", "new-key").json()
    assert same["summary"]["rows_error"] == 3
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["held_candidates"] == 2
    assert dashboard["unassignable_rows"] == 2


def test_cross_institution_and_officer_read_only(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    commit(client, headers, batch["id"])
    record = client.get("/api/v1/enrolments", headers=headers).json()["items"][0]
    other = login(client, "collegeb@example.test")
    for suffix in ["", "/rows", "/errors.csv"]:
        assert client.get(f"/api/v1/batches/{batch['id']}{suffix}", headers=other).status_code == 404
    assert commit(client, other, batch["id"]).status_code == 404
    assert client.post(f"/api/v1/batches/{batch['id']}/discard", headers=other).status_code == 404
    assert client.get(f"/api/v1/enrolments/{record['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/enrolments", headers=other).json()["total"] == 0
    assert client.get("/api/v1/dashboard", headers=other).json()["active"] == 0
    officer = login(client, "officer@example.test")
    assert client.get("/api/v1/dashboard", headers=officer).json()["active"] == 6
    assert commit(client, officer, batch["id"]).status_code == 403
    assert "student_name" not in client.get("/api/v1/enrolments", headers=officer).text


def test_outage_and_recovery(client, headers, fixtures_path):
    client.app.state.settings.mock_registry_outage = True
    batch = upload(client, headers, fixtures_path).json()
    assert batch["summary"]["identity_counts"] == {"PENDING_CHECK": 4, "MISSING": 1, "INVALID": 1}
    assert commit(client, headers, batch["id"]).status_code == 200
    client.app.state.settings.mock_registry_outage = False
    response = client.post("/api/v1/enrolments/recheck-identities", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"checked": 4, "resolved": 4, "remaining": 0}
    counts = client.get("/api/v1/dashboard", headers=headers).json()["identity_counts"]
    assert counts == {"VERIFIED": 1, "MISSING": 1, "INVALID": 3, "PENDING_CHECK": 1}


def test_lifecycle_and_stale_edit(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    commit(client, headers, batch["id"])
    record = client.get("/api/v1/enrolments", headers=headers).json()["items"][0]
    payload = {"expected_version": 1, "status": "WITHDRAWN", "end_date": "2026-09-01"}
    response = client.patch(f"/api/v1/enrolments/{record['id']}", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    assert (
        client.patch(f"/api/v1/enrolments/{record['id']}", headers=headers, json=payload).status_code == 409
    )
    assert client.get("/api/v1/dashboard", headers=headers).json()["active"] == 5
    assert len(client.get(f"/api/v1/enrolments/{record['id']}", headers=headers).json()["history"]) == 2


def test_transaction_failure_rolls_back(client, headers, fixtures_path, monkeypatch):
    batch = upload(client, headers, fixtures_path).json()

    def fail(*args):
        raise RuntimeError("test-only injected failure")

    monkeypatch.setattr(services, "history", fail)
    assert commit(client, headers, batch["id"]).status_code == 500
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        assert db.scalar(select(func.count()).select_from(Person)) == 0
        assert db.scalar(select(func.count()).select_from(History)) == 0
        assert (
            db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "BATCH_COMMITTED")) == 0
        )
    assert client.get(f"/api/v1/batches/{batch['id']}", headers=headers).json()["status"] == "DRY_RUN_READY"


def test_concurrent_commit_only_writes_once(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: commit(client, headers, batch["id"]), range(2)))
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json()["result"] == responses[1].json()["result"]
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 6
    with Session(client.app.state.engine) as db:
        assert (
            db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "BATCH_COMMITTED")) == 1
        )


def test_crypto_and_safe_logs(client, headers, fixtures_path, caplog):
    crypto = Crypto(client.app.state.settings)
    encrypted = crypto.encrypt({"name": "Synthetic Student"})
    assert crypto.decrypt(encrypted)["name"] == "Synthetic Student"
    with pytest.raises(InvalidTag):
        crypto.decrypt(encrypted[:-1] + bytes([encrypted[-1] ^ 1]))
    caplog.set_level("INFO", logger="apaar.requests")
    batch = upload(client, headers, fixtures_path).json()
    commit(client, headers, batch["id"])
    events = client.get("/api/v1/audit-events", headers=headers).text
    for sensitive in [
        "Demo Student 001",
        "2005-01-01",
        "900000000001",
        TEST_PASSWORD,
        headers["Authorization"][7:],
    ]:
        assert sensitive not in caplog.text
        assert sensitive not in events


def test_seed_is_repeatable(client):
    from app.seed import seed

    with Session(client.app.state.engine) as db:
        seed(db, "A-different-password-should-not-reset-accounts")
        assert db.scalar(select(func.count()).select_from(User)) == 3
        assert db.scalar(select(func.count()).select_from(Institution)) == 2
    assert login(client)


def test_max_supported_file(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "max-supported.csv")
    assert batch.status_code == 201, batch.text
    assert batch.json()["summary"]["rows_total"] == 500
    assert commit(client, headers, batch.json()["id"]).status_code == 200
    assert client.get("/api/v1/dashboard", headers=headers).json()["active"] == 500


@pytest.mark.parametrize(
    "content",
    [b"", b"wrong,header\n1,2", b"\xff\x00", b"x" * (2 * 1024 * 1024 + 1)],
    ids=["empty", "wrong-header", "binary", "oversize"],
)
def test_invalid_files(client, headers, content):
    response = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "invalid"},
        data={"academic_year": "2026-27"},
        files={"file": ("bad.csv", content, "text/csv")},
    )
    assert response.status_code in (400, 413), response.text


def test_duplicate_rows_and_discard(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "duplicate-keys.csv").json()
    assert batch["summary"]["rows_error"] == 2
    assert client.post(f"/api/v1/batches/{batch['id']}/discard", headers=headers).status_code == 200
    assert commit(client, headers, batch["id"]).status_code == 409
