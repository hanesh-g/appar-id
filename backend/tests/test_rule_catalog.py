import ast
import copy
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from conftest import commit, login, upload
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import rule_catalog
from app.config import ROOT
from app.models import Batch, Enrolment, RulePack
from app.registry import MESSAGES


def test_populated_upgrade_preserves_batch_report_and_pins_legacy_rules(client):
    schema = "rules_upgrade_" + uuid4().hex
    institution, batch = str(uuid4()), str(uuid4())
    config = Config(str(ROOT / "backend" / "alembic.ini"))
    with client.app.state.engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET search_path TO "{schema}"'))
        config.attributes["connection"] = connection
        command.upgrade(config, "b1c8389874af")
        connection.execute(
            text(
                "INSERT INTO institutions(id,name,reference) VALUES (:id,'Synthetic upgrade institution','UPGRADE')"
            ),
            {"id": institution},
        )
        connection.execute(
            text(
                "INSERT INTO upload_batches(id,institution_id,academic_year,filename,file_hash,idempotency_key,status,summary,result,created_at) VALUES (:id,:institution,'2026-27','historical.csv',:hash,'legacy','DRY_RUN_READY',CAST(:summary AS json),NULL,CURRENT_TIMESTAMP)"
            ),
            {
                "id": batch,
                "institution": institution,
                "hash": "0" * 64,
                "summary": '{"rows_total":3,"rows_error":1}',
            },
        )
        command.upgrade(config, "head")
        row = connection.execute(
            text("SELECT rule_set_id,summary FROM upload_batches WHERE id=:id"), {"id": batch}
        ).one()
        assert row.rule_set_id == "legacy-core-3fec502"
        assert row.summary == {"rows_total": 3, "rows_error": 1}
        pack = connection.execute(
            text("SELECT content,content_hash FROM rule_packs WHERE id=:id"), {"id": row.rule_set_id}
        ).one()
        assert rule_catalog.content_hash(pack.content) == pack.content_hash
        command.downgrade(config, "base")
        connection.execute(text('SET search_path TO "public"'))
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


def test_rule_catalog_covers_emitted_codes_and_requires_auth(client, headers):
    assert client.get("/api/v1/rules").status_code == 401
    response = client.get("/api/v1/rules", headers=headers)
    assert response.status_code == 200
    rules = response.json()["rules"]
    codes = set(MESSAGES)
    for name in ("rules.py", "services.py"):
        tree = ast.parse((Path(__file__).parents[1] / "app" / name).read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "issue"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                codes.add(node.args[0].value)
    # DATE_INVALID / FIELD_INVALID are selected by an expression rather than a literal call.
    codes |= {"DATE_INVALID", "FIELD_INVALID", "IDENTITY_CONFLICT"}
    assert codes <= rules.keys()
    assert all(r["review_status"] == "DEMO_ASSUMPTION" and r["reviewed_date"] is None for r in rules.values())
    assert client.get("/api/v1/rules/NOT_A_RULE", headers=headers).status_code == 404
    assert client.get("/api/v1/rules/DATE_INVALID?rule_set_id=absent", headers=headers).status_code == 404
    officer = login(client, "officer@example.test")
    assert client.get("/api/v1/rules/DATE_INVALID", headers=officer).status_code == 200
    # Help reads must not create database rows.
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(RulePack)) == 0


def test_batch_retains_rule_snapshot_when_current_pack_changes(client, headers, fixtures_path, monkeypatch):
    batch = upload(client, headers, fixtures_path).json()
    original = client.get(
        f"/api/v1/rules/DATE_INVALID?rule_set_id={batch['rule_set_id']}", headers=headers
    ).json()
    new = rule_catalog.manifest("demo-core-next")
    new["rules"]["DATE_INVALID"]["explanation"] = "A future explanation"
    with Session(client.app.state.engine) as db:
        db.add(
            RulePack(
                id="demo-core-next",
                validator_version="core-v1",
                content=new,
                content_hash=rule_catalog.content_hash(new),
            )
        )
        db.commit()
    monkeypatch.setattr(rule_catalog, "CURRENT_RULE_SET", "demo-core-next")
    assert (
        client.get("/api/v1/rules/DATE_INVALID", headers=headers).json()["explanation"]
        == "A future explanation"
    )
    assert (
        client.get(f"/api/v1/rules/DATE_INVALID?rule_set_id={batch['rule_set_id']}", headers=headers).json()
        == original
    )
    assert commit(client, headers, batch["id"]).status_code == 200


def test_unsupported_rule_execution_and_tampered_snapshot_fail_closed(client, headers, fixtures_path):
    batch = upload(client, headers, fixtures_path).json()
    unsupported = rule_catalog.manifest("unsupported")
    unsupported["validator_version"] = "unavailable-v99"
    with Session(client.app.state.engine) as db:
        db.add(
            RulePack(
                id="unsupported",
                validator_version="unavailable-v99",
                content=unsupported,
                content_hash=rule_catalog.content_hash(unsupported),
            )
        )
        db.flush()
        db.get(Batch, batch["id"]).rule_set_id = "unsupported"
        db.commit()
    response = commit(client, headers, batch["id"])
    assert response.status_code == 409 and response.json()["code"] == "RULESET_UNAVAILABLE"
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Enrolment)) == 0
        pack = db.get(RulePack, batch["rule_set_id"])
        changed = copy.deepcopy(pack.content)
        changed["rules"]["DATE_INVALID"]["explanation"] = "Tampered data"
        pack.content = changed
        db.commit()
    assert client.get(f"/api/v1/rules?rule_set_id={batch['rule_set_id']}", headers=headers).status_code == 503
