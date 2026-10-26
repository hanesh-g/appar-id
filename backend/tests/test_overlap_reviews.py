import csv
import io
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import commit, login
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import OverlapEvent, OverlapReview, User
from app.reconcile_intervals import reconcile_existing


def record(client, headers, fixtures_path, patch=None, key="interval"):
    reader = csv.DictReader(io.StringIO((fixtures_path / "intake-65.csv").read_text()))
    raw = {**next(reader), **(patch or {})}
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerow(raw)
    batch = client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": key},
        data={"academic_year": "2026-27"},
        files={"file": ("interval.csv", output.getvalue(), "text/csv")},
    )
    assert batch.status_code == 201, batch.text
    saved = commit(client, headers, batch.json()["id"])
    assert saved.status_code == 200, saved.text
    return client.get("/api/v1/enrolments?search=STU-001", headers=headers).json()["items"][0]


@pytest.mark.parametrize(
    ("end_a", "start_b", "expected"),
    [("2026-08-31", "2026-09-01", 0), ("2026-09-01", "2026-09-01", 1), ("2026-09-15", "2026-09-01", 1)],
)
def test_historical_intervals_and_sequential_transfer_boundaries(
    client, headers, fixtures_path, end_a, start_b, expected
):
    record(client, headers, fixtures_path, {"status": "COMPLETED", "end_date": end_a})
    other = login(client, "collegeb@example.test")
    record(client, other, fixtures_path, {"start_date": start_b})
    officer = login(client, "officer@example.test")
    reviews = client.get("/api/v1/overlap-reviews", headers=officer).json()
    assert reviews["total"] == expected
    if expected:
        assert reviews["items"][0]["overlap_start"] == start_b


def test_overlap_review_permissions_and_institution_notice_do_not_leak_pair(client, headers, fixtures_path):
    own = record(client, headers, fixtures_path)
    other = login(client, "collegeb@example.test")
    record(client, other, fixtures_path)
    officer = login(client, "officer@example.test")
    result = client.get("/api/v1/overlap-reviews", headers=officer)
    assert result.status_code == 200
    review = result.json()["items"][0]
    assert (
        "Demo Student 001" not in result.text
        and "900000000001" not in result.text
        and "2005-01-01" not in result.text
    )
    for actor in (headers, other):
        assert client.get("/api/v1/overlap-reviews", headers=actor).status_code == 403
        assert client.get(f"/api/v1/overlap-reviews/{review['id']}", headers=actor).status_code == 403
    detail = client.get(f"/api/v1/enrolments/{own['id']}", headers=headers)
    assert detail.json()["overlap_review_pending"] is True
    assert review["id"] not in detail.text and "Riverdale Technical College" not in detail.text
    assert review["id"] not in client.get("/api/v1/audit-events", headers=headers).text
    decided = client.patch(
        f"/api/v1/overlap-reviews/{review['id']}",
        headers=officer,
        json={"expected_version": 1, "status": "REVIEWED_PERMITTED_DUAL", "reason": "DEMO_DUAL_REVIEW"},
    )
    assert decided.status_code == 200 and decided.json()["version"] == 2
    assert (
        client.get(f"/api/v1/enrolments/{own['id']}", headers=headers).json()["overlap_review_pending"]
        is False
    )
    assert (
        client.patch(
            f"/api/v1/overlap-reviews/{review['id']}",
            headers=officer,
            json={"expected_version": 1, "status": "ESCALATED", "reason": "NEEDS_MORE_EVIDENCE"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/v1/enrolments/{own['id']}",
            headers=officer,
            json={"expected_version": 1, "status": "WITHDRAWN", "end_date": "2026-09-01"},
        ).status_code
        == 403
    )


def test_review_closes_and_reopens_when_actual_intervals_change(client, headers, fixtures_path):
    own = record(client, headers, fixtures_path)
    other = login(client, "collegeb@example.test")
    record(client, other, fixtures_path, {"start_date": "2026-09-01"})
    officer = login(client, "officer@example.test")
    review = client.get("/api/v1/overlap-reviews", headers=officer).json()["items"][0]
    assert (
        client.patch(
            f"/api/v1/enrolments/{own['id']}",
            headers=headers,
            json={"expected_version": 1, "status": "TRANSFERRED", "end_date": "2026-08-31"},
        ).status_code
        == 200
    )
    closed = client.get(f"/api/v1/overlap-reviews/{review['id']}", headers=officer).json()
    assert closed["status"] == "NO_LONGER_OVERLAPPING" and len(closed["events"]) == 2
    assert (
        client.patch(
            f"/api/v1/enrolments/{own['id']}",
            headers=headers,
            json={"expected_version": 2, "status": "ENROLLED", "end_date": None},
        ).status_code
        == 200
    )
    reopened = client.get(f"/api/v1/overlap-reviews/{review['id']}", headers=officer).json()
    assert reopened["status"] == "OPEN" and reopened["version"] == 3
    assert len(reopened["events"]) == 3


def test_similar_unverified_records_are_not_linked(client, headers, fixtures_path):
    record(client, headers, fixtures_path)
    other = login(client, "collegeb@example.test")
    record(client, other, fixtures_path, {"apaar_id": ""})
    officer = login(client, "officer@example.test")
    assert client.get("/api/v1/overlap-reviews", headers=officer).json()["total"] == 0


def test_concurrent_verified_commits_and_repeated_upload_do_not_duplicate_pair(
    client, headers, fixtures_path
):
    other = login(client, "collegeb@example.test")
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda actor: record(client, actor, fixtures_path), (headers, other)))
    record(client, headers, fixtures_path, key="repeat")
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(OverlapReview)) == 1
        assert db.scalar(select(func.count()).select_from(OverlapEvent)) == 1


def test_explicit_backfill_finds_preexisting_records_without_duplicate_decisions(
    client, headers, fixtures_path
):
    record(client, headers, fixtures_path)
    other = login(client, "collegeb@example.test")
    record(client, other, fixtures_path)
    with Session(client.app.state.engine) as db:
        for event in db.scalars(select(OverlapEvent)):
            db.delete(event)
        db.flush()
        for review in db.scalars(select(OverlapReview)):
            db.delete(review)
        db.commit()
        officer = db.scalar(select(User).where(User.role == "officer"))
        assert reconcile_existing(db, officer)["reviews"] == 1
        assert reconcile_existing(db, officer)["reviews"] == 1
        assert db.scalar(select(func.count()).select_from(OverlapEvent)) == 1
