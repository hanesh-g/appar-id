import base64
import secrets
from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import login
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit_integrity
from app.models import Audit, AuditChainHead, Programme


def create(client, headers, name="Audit programme"):
    return client.post(
        "/api/v1/programmes",
        headers=headers,
        json={"name": name, "academic_year": "2026-27", "approved_intake": 10},
    )


def verification(client, officer):
    return client.get("/api/v1/audit-events/verify", headers=officer)


def test_schema_only_bootstrap_and_officer_scope(client, headers):
    with Session(client.app.state.engine) as db:
        assert db.get(AuditChainHead, 1) is None
    assert create(client, headers).status_code == 201
    officer = login(client, "officer@example.test")
    checked = verification(client, officer)
    assert checked.status_code == 200 and checked.json()["verified"]
    assert checked.json()["checked_events"] == 1 and checked.json()["through_sequence"] == 1
    assert verification(client, headers).status_code == 403
    assert "sequence_no" not in client.get("/api/v1/audit-events", headers=headers).text


def test_concurrent_first_writers_create_one_head_and_contiguous_chain(client, headers):
    other = login(client, "collegeb@example.test")
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda actor: create(client, actor), (headers, other)))
    assert [r.status_code for r in responses] == [201, 201]
    officer = login(client, "officer@example.test")
    result = verification(client, officer).json()
    assert result["verified"] and result["checked_events"] == 2
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AuditChainHead)) == 1
        assert db.scalars(select(Audit.sequence_no).order_by(Audit.sequence_no)).all() == [1, 2]


@pytest.mark.parametrize(
    ("tamper", "broken"), [("action", 2), ("metadata", 2), ("middle", 2), ("tail", 3), ("head", None)]
)
def test_tampered_event_or_deleted_link_is_detected(client, headers, tamper, broken):
    for index in range(3):
        assert create(client, headers, f"Chain event {index}").status_code == 201
    officer = login(client, "officer@example.test")
    assert verification(client, officer).json()["verified"]
    with Session(client.app.state.engine) as db:
        item = db.scalar(select(Audit).where(Audit.sequence_no == (3 if tamper == "tail" else 2)))
        if tamper == "action":
            item.action = "ALTERED_EVENT"
        elif tamper == "metadata":
            item.details = {"altered": True}
        elif tamper in {"middle", "tail"}:
            db.delete(item)
        else:
            db.get(AuditChainHead, 1).last_hash = "f" * 64
        db.commit()  # Simulated database attacker: no service audit is queued.
    result = verification(client, officer).json()
    assert not result["verified"]
    if broken is not None:
        assert result["first_broken_sequence"] == broken


def test_audit_failure_rolls_back_business_event_and_genesis(client, headers, monkeypatch):
    original = audit_integrity.signed_hash

    def fail(*args):
        raise RuntimeError("Test-only signing failure")

    monkeypatch.setattr(audit_integrity, "signed_hash", fail)
    assert create(client, headers, "Rollback audit").status_code == 500
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Programme)) == 4
        assert db.scalar(select(func.count()).select_from(Audit)) == 0
        assert db.get(AuditChainHead, 1) is None
    monkeypatch.setattr(audit_integrity, "signed_hash", original)
    assert create(client, headers, "Rollback audit").status_code == 201
    assert verification(client, login(client, "officer@example.test")).json()["checked_events"] == 1


def test_missing_head_cannot_reset_an_existing_chain(client, headers):
    assert create(client, headers).status_code == 201
    with Session(client.app.state.engine) as db:
        db.delete(db.get(AuditChainHead, 1))
        db.commit()
    response = create(client, headers, "Head reset refused")
    assert response.status_code == 503 and response.json()["code"] == "AUDIT_HEAD_MISSING"
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Audit)) == 1
        assert db.scalar(select(func.count()).select_from(Programme)) == 5


def test_legacy_snapshot_is_attested_at_activation_and_disabled_chain_cannot_silently_resume(client, headers):
    client.app.state.settings.audit_chain_enabled = False
    assert create(client, headers, "Legacy event").status_code == 201
    client.app.state.settings.audit_chain_enabled = True
    assert create(client, headers, "First chained event").status_code == 201
    officer = login(client, "officer@example.test")
    result = verification(client, officer).json()
    assert result["verified"] and result["legacy_events"] == 1 and result["checked_events"] == 1
    client.app.state.settings.audit_chain_enabled = False
    assert create(client, headers, "Downgrade refused").status_code == 503
    client.app.state.settings.audit_chain_enabled = True
    assert verification(client, officer).json()["verified"]
    with Session(client.app.state.engine) as db:
        db.scalar(select(Audit).where(Audit.sequence_no.is_(None))).details = {
            "changed_after_activation": True
        }
        db.commit()
    result = verification(client, officer).json()
    assert not result["verified"] and result["reason"] == "BASELINE_MISMATCH"


def test_wrong_key_fails_verification_and_blocks_append(client, headers):
    assert create(client, headers).status_code == 201
    officer = login(client, "officer@example.test")
    original = client.app.state.settings.audit_hmac_key
    client.app.state.settings.audit_hmac_key = SecretStr(base64.b64encode(secrets.token_bytes(32)).decode())
    assert not verification(client, officer).json()["verified"]
    assert create(client, headers, "Wrong key refused").status_code == 503
    client.app.state.settings.audit_hmac_key = original
    assert verification(client, officer).json()["verified"]


def test_verification_during_commits_has_consistent_watermark(client, headers):
    assert create(client, headers, "Initial snapshot event").status_code == 201
    officer = login(client, "officer@example.test")

    def write():
        for index in range(4):
            assert create(client, headers, f"Concurrent event {index}").status_code == 201

    with ThreadPoolExecutor(max_workers=2) as pool:
        writing = pool.submit(write)
        for _ in range(3):
            result = verification(client, officer).json()
            assert result["verified"] and result["checked_events"] == result["through_sequence"]
        writing.result(timeout=15)
    assert verification(client, officer).json()["checked_events"] == 5
