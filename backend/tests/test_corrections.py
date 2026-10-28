import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from conftest import commit, login, upload
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from test_resolution_cases import staged_case

from app import corrections, services
from app.db import utcnow
from app.models import (
    Batch,
    BatchRow,
    CorrectionOrigin,
    CorrectionProposal,
    Enrolment,
    Person,
    ResolutionCase,
)


def propose(client, headers, case, changes=None):
    response = client.post(
        f"/api/v1/resolution-cases/{case['id']}/correction-previews",
        headers=headers,
        json={"expected_version": case["version"], "changes": changes or {"start_date": "2026-07-15"}},
    )
    assert response.status_code == 201, response.text
    return response.json()


def apply(client, headers, proposal):
    return client.post(
        f"/api/v1/correction-proposals/{proposal['id']}/apply",
        headers=headers,
        json={"expected_version": proposal["case_version"]},
    )


def test_held_row_apply_reduces_current_work_and_retains_original_snapshot(client, headers, fixtures_path):
    batch, row, case = staged_case(client, headers, fixtures_path)
    with Session(client.app.state.engine) as db:
        original = db.get(BatchRow, row["id"]).raw_enc
    assert client.get("/api/v1/dashboard", headers=headers).json()["held_candidates"] == 2
    proposal = propose(client, headers, case)
    assert proposal["outcome"] == {"created": 1, "updated": 0, "unchanged": 0, "held": 0}
    assert proposal["active_delta"] == 1 and proposal["can_apply"]
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 0
    result = apply(client, headers, proposal)
    assert result.status_code == 200, result.text
    assert result.json()["created"] == 1 and result.json()["case_status"] == "RESOLVED"
    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["active"] == 1 and dashboard["held_candidates"] == 1
    assert dashboard["unassignable_rows"] == 1
    assert client.get(f"/api/v1/batches/{batch['id']}", headers=headers).json()["summary"] == batch["summary"]
    with Session(client.app.state.engine) as db:
        source = db.get(BatchRow, row["id"])
        assert source.status == "SUPERSEDED_BY_CORRECTION" and source.raw_enc == original
        assert db.scalar(select(func.count()).select_from(CorrectionOrigin)) == 1
    assert apply(client, headers, proposal).json() == result.json()


def test_exact_proposal_scope_expiry_and_input_tampering(client, headers, fixtures_path):
    _, _, case = staged_case(client, headers, fixtures_path)
    proposal = propose(client, headers, case)
    other = login(client, "collegeb@example.test")
    assert apply(client, other, proposal).status_code == 404
    assert (
        client.get(f"/api/v1/resolution-cases/{case['id']}/correction-context", headers=other).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/correction-proposals/{proposal['id']}/apply",
            headers=headers,
            json={"expected_version": 1, "changes": {"start_date": "2020-01-01"}},
        ).status_code
        == 422
    )
    with Session(client.app.state.engine) as db:
        db.get(CorrectionProposal, proposal["id"]).expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert apply(client, headers, proposal).status_code == 409
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0


@pytest.mark.parametrize("change", ["case", "intake", "payload"])
def test_changed_case_intake_or_encrypted_payload_refuses_apply(client, headers, fixtures_path, change):
    _, _, case = staged_case(client, headers, fixtures_path)
    proposal = propose(client, headers, case)
    if change == "case":
        assert (
            client.patch(
                f"/api/v1/resolution-cases/{case['id']}",
                headers=headers,
                json={"expected_version": 1, "status": "WAITING_ON_USER", "owner_type": "STUDENT_ACTION"},
            ).status_code
            == 200
        )
    elif change == "intake":
        programme = client.get("/api/v1/programmes", headers=headers).json()[0]
        assert (
            client.patch(
                f"/api/v1/programmes/{programme['id']}", headers=headers, json={"approved_intake": 59}
            ).status_code
            == 200
        )
    else:
        with Session(client.app.state.engine) as db:
            record = db.get(CorrectionProposal, proposal["id"])
            record.payload_enc = record.payload_enc[:-1] + bytes([record.payload_enc[-1] ^ 1])
            db.commit()
    result = apply(client, headers, proposal)
    assert result.status_code == (403 if change == "intake" else 409), result.text
    if change == "intake":
        assert result.json()["code"] == "PROGRAMME_APPROVAL_REQUIRED"
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        assert db.scalar(select(func.count()).select_from(Batch)) == 1
        assert db.get(CorrectionProposal, proposal["id"]).result is None


def test_structurally_invalid_proposal_cannot_apply(client, headers, fixtures_path):
    _, _, case = staged_case(client, headers, fixtures_path)
    proposal = propose(client, headers, case, {"start_date": "still-invalid"})
    assert not proposal["can_apply"] and proposal["outcome"]["held"] == 1
    assert apply(client, headers, proposal).status_code == 422


def test_old_batch_cannot_overwrite_a_new_inline_correction(client, headers, fixtures_path):
    _, row, case = staged_case(client, headers, fixtures_path)
    context = client.get(f"/api/v1/resolution-cases/{case['id']}/correction-context", headers=headers).json()
    raw = {**context["fields"], "start_date": "2026-07-14"}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(raw))
    writer.writeheader()
    writer.writerow(raw)
    stale = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": "stale-inline"},
        data={"academic_year": "2026-27"},
        files={"file": ("earlier.csv", buffer.getvalue(), "text/csv")},
    ).json()
    proposal = propose(client, headers, case)
    assert apply(client, headers, proposal).status_code == 200
    response = commit(client, headers, stale["id"])
    assert response.status_code == 409 and response.json()["code"] == "STALE_PREVIEW"
    assert client.get("/api/v1/enrolments", headers=headers).json()["items"][0]["start_date"] == "2026-07-15"


def test_concurrent_apply_is_once_and_rolls_back_if_case_event_fails(
    client, headers, fixtures_path, monkeypatch
):
    _, row, case = staged_case(client, headers, fixtures_path)
    proposal = propose(client, headers, case)
    original = corrections.case_event

    def fail(*args):
        raise RuntimeError("Test-only case event failure")

    monkeypatch.setattr(corrections, "case_event", fail)
    assert apply(client, headers, proposal).status_code == 500
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        assert db.scalar(select(func.count()).select_from(Person)) == 0
        assert db.get(BatchRow, row["id"]).status == "HELD"
        assert db.get(ResolutionCase, case["id"]).status == "OPEN"
        assert db.get(CorrectionProposal, proposal["id"]).result is None
    monkeypatch.setattr(corrections, "case_event", original)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: apply(client, headers, proposal), range(2)))
    assert [r.status_code for r in results] == [200, 200]
    assert results[0].json() == results[1].json()
    assert client.get("/api/v1/enrolments", headers=headers).json()["total"] == 1


def test_parallel_identity_promotions_follow_digest_before_enrolment_locks(
    client, headers, fixtures_path, monkeypatch
):
    reader = csv.DictReader(io.StringIO((fixtures_path / "intake-65.csv").read_text()))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerow(next(reader))
    other = login(client, "collegeb@example.test")
    client.app.state.settings.mock_registry_outage = True
    for actor in (headers, other):
        response = client.post(
            "/api/v1/batches",
            headers={**actor, "Idempotency-Key": "promotion"},
            data={"academic_year": "2026-27"},
            files={"file": ("promotion.csv", buffer.getvalue(), "text/csv")},
        )
        assert commit(client, actor, response.json()["id"]).status_code == 200
    client.app.state.settings.mock_registry_outage = False
    original = services.lock_identity_keys

    def bounded(db, *args, **kwargs):
        db.execute(text("SET LOCAL lock_timeout = '3s'"))
        return original(db, *args, **kwargs)

    monkeypatch.setattr(services, "lock_identity_keys", bounded)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda actor: client.post("/api/v1/enrolments/recheck-identities", headers=actor),
                (headers, other),
            )
        )
    assert [r.status_code for r in results] == [200, 200]
    with Session(client.app.state.engine) as db:
        records = db.scalars(select(Enrolment)).all()
        assert all(r.identity_status == "VERIFIED" for r in records)
        assert len({r.person_id for r in records}) == 1


def test_preview_and_case_audit_never_include_plain_identity_values(client, headers, fixtures_path, caplog):
    _, _, case = staged_case(client, headers, fixtures_path)
    proposal = propose(
        client,
        headers,
        case,
        {
            "start_date": "2026-07-15",
            "student_name": "Sensitive Synthetic Name",
            "date_of_birth": "2004-02-03",
        },
    )
    result = apply(client, headers, proposal)
    assert result.status_code == 200
    events = client.get("/api/v1/audit-events", headers=headers).text
    for value in ("Demo Student 080", "900000000080", "2005-01-01", "Sensitive Synthetic Name", "2004-02-03"):
        assert value not in str(proposal)
        assert value not in events and value not in caplog.text


@pytest.mark.parametrize("stale_target", [False, True])
def test_existing_missing_identity_promotes_without_count_inflation_or_stale_overwrite(
    client, headers, fixtures_path, stale_target
):
    batch = upload(client, headers, fixtures_path, "intake-65.csv").json()
    assert commit(client, headers, batch["id"]).status_code == 200
    record = client.get("/api/v1/enrolments?search=STU-061", headers=headers).json()["items"][0]
    case = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"enrolment_id": record["id"], "issue_code": "APAAR_MISSING"},
    ).json()
    proposal = propose(client, headers, case, {"apaar_id": "900000000061"})
    assert proposal["outcome"]["updated"] == 1 and proposal["active_delta"] == 0
    if stale_target:
        assert (
            client.patch(
                f"/api/v1/enrolments/{record['id']}",
                headers=headers,
                json={"expected_version": 1, "status": "WITHDRAWN", "end_date": "2026-09-01"},
            ).status_code
            == 200
        )
        assert apply(client, headers, proposal).status_code == 409
        assert (
            client.get(f"/api/v1/enrolments/{record['id']}", headers=headers).json()["status"] == "WITHDRAWN"
        )
    else:
        result = apply(client, headers, proposal)
        assert result.status_code == 200, result.text
        assert result.json()["updated"] == 1 and result.json()["created"] == 0
        dashboard = client.get("/api/v1/dashboard", headers=headers).json()
        assert dashboard["active"] == 65 and dashboard["identity_counts"]["VERIFIED"] == 61


def test_unchanged_inline_apply_does_not_increment_enrolment_version(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path, "intake-65.csv").json()
    assert commit(client, headers, batch["id"]).status_code == 200
    record = client.get("/api/v1/enrolments?search=STU-061", headers=headers).json()["items"][0]
    case = client.post(
        "/api/v1/resolution-cases",
        headers=headers,
        json={"enrolment_id": record["id"], "issue_code": "APAAR_MISSING"},
    ).json()
    proposal = propose(client, headers, case, {"apaar_id": ""})
    assert proposal["outcome"]["unchanged"] == 1
    response = apply(client, headers, proposal)
    assert response.status_code == 200 and response.json()["unchanged"] == 1
    assert response.json()["case_status"] != "RESOLVED"
    assert client.get(f"/api/v1/enrolments/{record['id']}", headers=headers).json()["version"] == 1
