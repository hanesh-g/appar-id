"""Exercise real core routes with future/unknown principals before adding roles."""

from uuid import uuid4

import pytest
from conftest import commit, login, upload
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import authenticated
from app.errors import DomainError
from app.models import Audit, Enrolment, Institution, Programme, User
from app.repositories import owned, query_scope


def route_requests(batch_id, programme_id, enrolment_id, content):
    """Valid paths/payloads ensure permission denial is not just validation failure."""
    return [
        ("GET", "/auth/me", {}),
        ("GET", "/institutions", {}),
        ("GET", "/programmes", {}),
        ("GET", "/templates/students.csv", {}),
        ("GET", f"/batches/{batch_id}", {}),
        ("GET", f"/batches/{batch_id}/rows", {}),
        ("GET", f"/batches/{batch_id}/errors.csv", {}),
        ("GET", "/dashboard", {}),
        ("GET", "/enrolments", {}),
        ("GET", f"/enrolments/{enrolment_id}", {}),
        ("GET", "/audit-events", {}),
        ("GET", "/rules", {}),
        ("GET", "/rules/DATE_INVALID", {}),
        (
            "POST",
            "/programmes",
            {"json": {"name": "New programme", "academic_year": "2026-27", "approved_intake": 10}},
        ),
        ("PATCH", f"/programmes/{programme_id}", {"json": {"approved_intake": 1}}),
        (
            "POST",
            "/batches",
            {"data": {"academic_year": "2026-27"}, "files": {"file": ("test.csv", content, "text/csv")}},
        ),
        ("POST", f"/batches/{batch_id}/commit", {"json": {"mode": "commit_valid"}}),
        ("POST", f"/batches/{batch_id}/discard", {}),
        ("POST", "/enrolments/recheck-identities", {}),
        (
            "PATCH",
            f"/enrolments/{enrolment_id}",
            {"json": {"expected_version": 1, "status": "WITHDRAWN", "end_date": "2026-09-01"}},
        ),
    ]


@pytest.mark.parametrize(
    ("role", "has_institution", "active"),
    [
        ("student", False, True),
        ("verifier", False, True),
        ("unrecognised_role", False, True),
        ("institution_admin", False, True),
        ("officer", True, True),
        ("officer", False, False),
    ],
)
def test_core_route_matrix_denies_unpermitted_principals(
    client, headers, fixtures_path, role, has_institution, active
):
    batch = upload(client, headers, fixtures_path).json()
    assert commit(client, headers, batch["id"]).status_code == 200
    programme = client.get("/api/v1/programmes", headers=headers).json()[0]
    record = client.get("/api/v1/enrolments", headers=headers).json()["items"][0]
    with Session(client.app.state.engine) as db:
        audit_before = db.scalar(select(func.count()).select_from(Audit))
    # This future authenticated principal is deliberately not persisted: the current
    # schema still allows only the two core roles. The real route guards must deny it.
    actor = User(
        id=str(uuid4()),
        role=role,
        active=active,
        institution_id=programme["institution_id"] if has_institution else None,
    )
    client.app.dependency_overrides[authenticated] = lambda: actor
    try:
        for method, path, options in route_requests(
            batch["id"], programme["id"], record["id"], (fixtures_path / "identity-cases.csv").read_bytes()
        ):
            response = client.request(
                method, "/api/v1" + path, headers={"Idempotency-Key": "denied-upload"}, **options
            )
            assert response.status_code == 403, (method, path, response.text)
            assert response.json()["code"] == "FORBIDDEN"
        assert client.get("/api/v1/health").status_code == 200
    finally:
        client.app.dependency_overrides.clear()
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Audit)) == audit_before
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 6
        with pytest.raises(DomainError) as denied:
            query_scope(select(Programme), Programme, actor)
        assert denied.value.status == 403
        with pytest.raises(DomainError):
            owned(db, Programme, programme["id"], actor)


def test_officer_reads_without_mutation_or_correction_export(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    assert commit(client, headers, batch["id"]).status_code == 200
    programme = client.get("/api/v1/programmes", headers=headers).json()[0]
    record = client.get("/api/v1/enrolments", headers=headers).json()["items"][0]
    officer = login(client, "officer@example.test")
    for method, path, options in route_requests(
        batch["id"], programme["id"], record["id"], (fixtures_path / "identity-cases.csv").read_bytes()
    ):
        response = client.request(
            method, "/api/v1" + path, headers={**officer, "Idempotency-Key": "officer-upload"}, **options
        )
        expected = 200 if method == "GET" and not path.endswith("errors.csv") else 403
        assert response.status_code == expected, (method, path, response.text)
    institutions = client.get("/api/v1/institutions", headers=officer).json()
    assert len(institutions) == 2
    assert "student_name" not in client.get("/api/v1/enrolments", headers=officer).text


def test_institution_lists_and_dashboard_filters_remain_scoped(client, headers):
    other = login(client, "collegeb@example.test")
    foreign = client.get("/api/v1/programmes", headers=other).json()[0]
    own = client.get("/api/v1/institutions", headers=headers).json()
    assert len(own) == 1 and own[0]["id"] != foreign["institution_id"]
    assert (
        client.get(
            "/api/v1/dashboard", headers=headers, params={"institution_id": foreign["institution_id"]}
        ).json()["programmes"]
        == []
    )
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Institution)) == 2
