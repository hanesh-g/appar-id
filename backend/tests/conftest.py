import base64
import os
import secrets
from datetime import date
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import services
from app.config import ROOT, Settings
from app.db import Base, make_engine
from app.main import create_app
from app.seed import seed

TEST_PASSWORD = "SyntheticTestOnly!2026"


@pytest.fixture(autouse=True)
def extension_test_keys(monkeypatch):
    # Independent, test-only secrets; never application defaults or production bindings.
    for name in ("AUDIT_HMAC_KEY", "GRANT_TOKEN_KEY"):
        monkeypatch.setenv(name, base64.b64encode(secrets.token_bytes(32)).decode())


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(services, "business_date", lambda: date(2026, 10, 25))
    values = dotenv_values(ROOT / ".env")
    url = os.environ.get("TEST_DATABASE_URL") or values.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test")
    engine = make_engine(url)
    if not engine.url.database or not engine.url.database.endswith("_test"):
        pytest.fail("Refusing to reset a database whose name does not end in _test")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        pytest.fail(
            "Cannot reach the dedicated test database. Check its service, credentials, and local-network permissions. Connection values are not printed.",
            pytrace=False,
        )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed(db, TEST_PASSWORD)
    settings = Settings().model_copy(update={"database_url": SecretStr(url), "mock_registry_outage": False})
    with TestClient(create_app(settings), raise_server_exceptions=False) as test_client:
        yield test_client
    engine.dispose()


def login(client, email="collegea@example.test"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


@pytest.fixture()
def headers(client):
    return login(client)


@pytest.fixture()
def fixtures_path():
    return Path(__file__).resolve().parents[2] / "fixtures"


def upload(client, headers, fixtures_path, name="identity-cases.csv", key="test-key"):
    return client.post(
        "/api/v1/batches",
        headers={**headers, "Idempotency-Key": key},
        data={"academic_year": "2026-27"},
        files={"file": (name, (fixtures_path / name).read_bytes(), "text/csv")},
    )


def commit(client, headers, batch_id, mode="commit_valid"):
    return client.post(f"/api/v1/batches/{batch_id}/commit", headers=headers, json={"mode": mode})
