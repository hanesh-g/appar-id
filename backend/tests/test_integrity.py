import csv
import io
from uuid import uuid4

from alembic import command
from alembic.config import Config
from conftest import commit, upload
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.config import ROOT
from app.models import Audit
from app.rules import safe_csv


def test_migration_upgrade_and_downgrade(client):
    schema = "migration_test_" + uuid4().hex
    config = Config(str(ROOT / "backend" / "alembic.ini"))
    with client.app.state.engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET search_path TO "{schema}"'))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        constraints = inspect(connection).get_check_constraints("enrolments", schema=schema)
        assert "enrolment_identity_link" in {c["name"] for c in constraints}
        assert "enrolment_status_end_date" in {c["name"] for c in constraints}
        command.downgrade(config, "base")
        assert "enrolments" not in inspect(connection).get_table_names(schema=schema)
        connection.execute(text('SET search_path TO "public"'))
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


def test_audit_matches_request_id(client, headers, fixtures_path):
    response = upload(client, headers, fixtures_path)
    with Session(client.app.state.engine) as db:
        event = db.scalar(select(Audit).where(Audit.entity_id == response.json()["id"]))
        assert event.request_id == response.headers["X-Request-ID"]


def test_identity_reassignment_requires_review(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    commit(client, headers, batch["id"])
    content = (
        (fixtures_path / "identity-cases.csv")
        .read_text()
        .replace("900000000001", "900000000010")
        .replace("Demo Student 001", "Demo Student 010")
    )
    response = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "reassign"},
        data={"academic_year": "2026-27"},
        files={"file": ("changed.csv", content, "text/csv")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["summary"]["issue_counts"]["IDENTITY_REASSIGNMENT"] == 1
    assert response.json()["summary"]["rows_error"] == 1


def test_duplicate_verified_identity_is_blocked(client, headers, fixtures_path):
    content = (fixtures_path / "intake-65.csv").read_text()
    reader = csv.DictReader(io.StringIO(content))
    first = next(reader)
    second = {**first, "student_ref": "ANOTHER-REFERENCE"}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows([first, second])
    response = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "identity-duplicate"},
        data={"academic_year": "2026-27"},
        files={"file": ("duplicate.csv", buffer.getvalue(), "text/csv")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["summary"]["rows_error"] == 2


def test_csv_export_does_not_execute_formulas():
    result = safe_csv([{"value": '=HYPERLINK("https://example.test")'}, {"value": "+SUM(1,2)"}], ["value"])
    rows = list(csv.DictReader(io.StringIO(result)))
    assert rows[0]["value"].startswith("'=")
    assert rows[1]["value"].startswith("'+")


def test_cors_is_exact(client):
    allowed = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    denied = client.get("/api/v1/health", headers={"Origin": "https://unexpected.example.test"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_programme_creation_edit_and_audit(client, headers):
    payload = {"name": "Mechanical Engineering", "academic_year": "2026-27", "approved_intake": 40}
    created = client.post("/api/v1/programmes", headers=headers, json=payload)
    assert created.status_code == 201
    assert client.post("/api/v1/programmes", headers=headers, json=payload).status_code == 409
    edited = client.patch(
        f"/api/v1/programmes/{created.json()['id']}", headers=headers, json={"approved_intake": 55}
    )
    assert edited.status_code == 200
    assert edited.json()["approved_intake"] == 55
    actions = [e["action"] for e in client.get("/api/v1/audit-events", headers=headers).json()["items"]]
    assert "PROGRAMME_CREATED" in actions and "INTAKE_UPDATED" in actions


def test_correction_export_and_filters(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    rows = client.get(f"/api/v1/batches/{batch['id']}/rows?code=APAAR_MISSING", headers=headers).json()
    assert rows["total"] == 1
    response = client.get(f"/api/v1/batches/{batch['id']}/errors.csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert len(list(csv.DictReader(io.StringIO(response.text)))) == 5


def test_new_conflict_refuses_stale_commit(client, headers, fixtures_path):
    reader = csv.DictReader(io.StringIO((fixtures_path / "intake-65.csv").read_text()))
    first = next(reader)

    def send(row, key):
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerow(row)
        return client.post(
            "/api/v1/batches",
            headers={**headers, "Idempotency-Key": key},
            data={"academic_year": "2026-27"},
            files={"file": ("one.csv", buffer.getvalue(), "text/csv")},
        ).json()

    original = send(first, "preview")
    concurrent = send({**first, "student_ref": "OTHER-REFERENCE"}, "concurrent")
    assert commit(client, headers, concurrent["id"]).status_code == 200
    stale = commit(client, headers, original["id"])
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_PREVIEW"
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 1


def test_row_limit_rejects_501st_row(client, headers, fixtures_path):
    content = (fixtures_path / "max-supported.csv").read_text()
    content += content.splitlines()[1] + "\n"
    response = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "too-many-rows"},
        data={"academic_year": "2026-27"},
        files={"file": ("oversize-rows.csv", content, "text/csv")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "ROW_LIMIT"
