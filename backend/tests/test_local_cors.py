import base64

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def cors_settings(mode, origins):
    return Settings(
        _env_file=None,
        app_env=mode,
        allowed_origins=origins,
        database_url="postgresql+psycopg://unused@127.0.0.1:1/unused",
        jwt_secret="synthetic-signing-key-for-cors-tests-only",
        pii_key=base64.b64encode(bytes([1]) * 32).decode(),
        hmac_key=base64.b64encode(bytes([2]) * 32).decode(),
    )


@pytest.mark.parametrize(
    ("configured", "requested"),
    [
        ("http://localhost:5173", "http://127.0.0.1:5173"),
        ("http://127.0.0.1:5173", "http://localhost:5173"),
    ],
)
def test_local_alias_accepts_authenticated_request_preflight(configured, requested):
    with TestClient(create_app(cors_settings("local", configured))) as http:
        response = http.options(
            "/api/v1/auth/login",
            headers={
                "Origin": requested,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == requested


@pytest.mark.parametrize("mode", ["local", "demo"])
def test_other_loopback_ports_and_external_origins_stay_blocked(mode):
    with TestClient(create_app(cors_settings(mode, "http://localhost:5173"))) as http:
        for origin in ["http://127.0.0.1:5174", "https://unexpected.example.test"]:
            response = http.options(
                "/api/v1/auth/login",
                headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
            )
            assert response.status_code == 400
            assert "access-control-allow-origin" not in response.headers


def test_hosted_mode_does_not_expand_the_allowlist():
    with TestClient(create_app(cors_settings("demo", "http://localhost:5173"))) as http:
        response = http.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST"},
        )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
