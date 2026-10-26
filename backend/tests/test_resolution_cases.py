from concurrent.futures import ThreadPoolExecutor

from conftest import commit, login, upload
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import resolution
from app.models import CaseEvent, CaseOrigin, Enrolment, ResolutionCase


def staged_case(client, headers, fixtures_path, key="case-source"):
    batch = upload(client, headers, fixtures_path, "structural-errors.csv", key).json()
    assert commit(client, headers, batch["id"]).status_code == 200
    rows = client.get(f"/api/v1/batches/{batch['id']}/rows", headers=headers).json()["items"]
    row = next(r for r in rows if any(i["code"] == "DATE_INVALID" for i in r["issues"]))
    response = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"batch_row_id": row["id"], "issue_code": "DATE_INVALID"},
    )
    assert response.status_code == 201, response.text
    return batch, row, response.json()


def test_staged_case_without_enrolment_deduplicates_origins(client, headers, fixtures_path):
    batch, row, case = staged_case(client, headers, fixtures_path)
    assert case["subject_kind"] == "STAGED_ROW" and case["enrolment_id"] is None
    repeated = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"batch_row_id": row["id"], "issue_code": "DATE_INVALID"},
    )
    assert repeated.json()["id"] == case["id"] and repeated.json()["version"] == 1
    second = staged_case(client, headers, fixtures_path, "other-source")[2]
    assert second["id"] == case["id"]
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        assert db.scalar(select(func.count()).select_from(ResolutionCase)) == 1
        assert db.scalar(select(func.count()).select_from(CaseEvent)) == 1
        assert db.scalar(select(func.count()).select_from(CaseOrigin)) == 2
    assert client.get(f"/api/v1/batches/{batch['id']}", headers=headers).json()["summary"] == batch["summary"]


def test_case_transitions_staleness_scope_and_false_closure(client, headers, fixtures_path):
    _, _, case = staged_case(client, headers, fixtures_path)
    url = f"/api/v1/resolution-cases/{case['id']}"
    waiting = client.patch(
        url,
        headers=headers,
        json={"expected_version": 1, "owner_type": "STUDENT_ACTION", "status": "WAITING_ON_USER"},
    )
    assert waiting.status_code == 200 and waiting.json()["version"] == 2
    assert (
        client.patch(url, headers=headers, json={"expected_version": 1, "status": "OPEN"}).status_code == 409
    )
    assert (
        client.patch(
            url, headers=headers, json={"expected_version": 2, "status": "READY_TO_RECHECK"}
        ).status_code
        == 200
    )
    assert (
        client.patch(url, headers=headers, json={"expected_version": 3, "status": "RESOLVED"}).status_code
        == 422
    )
    assert (
        client.patch(
            url, headers=headers, json={"expected_version": 3, "comment": "Do not store personal notes"}
        ).status_code
        == 422
    )
    other = login(client, "collegeb@example.test")
    assert client.get(url, headers=other).status_code == 404
    assert client.patch(url, headers=other, json={"expected_version": 3, "status": "OPEN"}).status_code == 404
    assert client.get("/api/v1/resolution-cases", headers=other).json()["total"] == 0
    officer = login(client, "officer@example.test")
    assert client.get("/api/v1/resolution-cases", headers=officer).status_code == 403
    current = client.get(url, headers=headers).json()
    assert current["status"] == "READY_TO_RECHECK" and len(current["events"]) == 3


def test_case_concurrent_transitions_do_not_overwrite(client, headers, fixtures_path):
    case = staged_case(client, headers, fixtures_path)[2]
    changes = [
        {"expected_version": 1, "owner_type": "STUDENT_ACTION", "status": "WAITING_ON_USER"},
        {"expected_version": 1, "owner_type": "UPSTREAM_AUTHORITY", "status": "WAITING_ON_AUTHORITY"},
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda data: client.patch(
                    f"/api/v1/resolution-cases/{case['id']}", headers=headers, json=data
                ),
                changes,
            )
        )
    assert sorted(r.status_code for r in results) == [200, 409]


def test_case_can_close_after_actual_mock_recheck_and_preserve_reopen_history(client, headers, fixtures_path):
    client.app.state.settings.mock_registry_outage = True
    batch = upload(client, headers, fixtures_path).json()
    commit(client, headers, batch["id"])
    record = client.get("/api/v1/enrolments?search=STU-001", headers=headers).json()["items"][0]
    created = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"enrolment_id": record["id"], "issue_code": "REGISTRY_UNAVAILABLE"},
    )
    assert created.status_code == 201, created.text
    url = f"/api/v1/resolution-cases/{created.json()['id']}"
    client.patch(url, headers=headers, json={"expected_version": 1, "status": "READY_TO_RECHECK"})
    assert (
        client.patch(url, headers=headers, json={"expected_version": 2, "status": "RESOLVED"}).status_code
        == 422
    )
    client.app.state.settings.mock_registry_outage = False
    assert client.post("/api/v1/enrolments/recheck-identities", headers=headers).status_code == 200
    closed = client.patch(url, headers=headers, json={"expected_version": 2, "status": "RESOLVED"})
    assert closed.status_code == 200 and closed.json()["evidence_kind"] == "MOCK"
    reopened = client.patch(url, headers=headers, json={"expected_version": 3, "status": "OPEN"})
    assert reopened.status_code == 200 and reopened.json()["episode"] == 2
    assert len(client.get(url, headers=headers).json()["events"]) == 4


def test_case_creation_and_event_roll_back_if_audit_fails(client, headers, fixtures_path, monkeypatch):
    batch = upload(client, headers, fixtures_path, "structural-errors.csv").json()
    row = client.get(f"/api/v1/batches/{batch['id']}/rows", headers=headers).json()["items"][0]

    def fail(*args):
        raise RuntimeError("Test-only audit failure")

    monkeypatch.setattr(resolution, "audit", fail)
    response = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"batch_row_id": row["id"], "issue_code": row["issues"][0]["code"]},
    )
    assert response.status_code == 500
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(ResolutionCase)) == 0
        assert db.scalar(select(func.count()).select_from(CaseEvent)) == 0
