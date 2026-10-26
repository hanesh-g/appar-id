import base64
from functools import cached_property
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", extra="ignore", case_sensitive=False, hide_input_in_errors=True
    )

    app_env: str = "local"
    database_url: SecretStr
    jwt_secret: SecretStr = Field(min_length=32)
    pii_key: SecretStr
    hmac_key: SecretStr
    jwt_issuer: str = "apaar-demo"
    jwt_audience: str = "apaar-web"
    allowed_origins: str = "http://localhost:5173"
    registry_mode: str = "mock"
    mock_registry_outage: bool = False
    demo_password: SecretStr | None = None
    audit_chain_enabled: bool = False
    audit_hmac_key: SecretStr | None = None
    audit_key_id: str = Field(default="audit-v1", pattern=r"^[A-Za-z0-9_.-]{1,40}$")

    @field_validator("registry_mode")
    @classmethod
    def mock_only(cls, value: str) -> str:
        if value != "mock":
            raise ValueError("Only simulated registry mode is implemented")
        return value

    @field_validator("pii_key", "hmac_key", "audit_hmac_key")
    @classmethod
    def valid_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return value
        try:
            if len(base64.b64decode(value.get_secret_value(), validate=True)) != 32:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Expected a base64-encoded 32-byte key") from None
        return value

    @model_validator(mode="after")
    def audit_key_required(self):
        if self.audit_chain_enabled and self.audit_hmac_key is None:
            raise ValueError("Enabled audit integrity requires AUDIT_HMAC_KEY")
        return self

    @cached_property
    def origins(self) -> list[str]:
        values = [v.strip().rstrip("/") for v in self.allowed_origins.split(",") if v.strip()]
        if "*" in values:
            raise ValueError("Use exact frontend origins, not a wildcard")
        if self.app_env == "local":
            # Vite prints 127.0.0.1 while existing local .env files use localhost.
            # Treat only these two exact development origins as aliases. Hosted
            # environments must continue to use their explicit allowlist.
            aliases = {
                "http://localhost:5173": "http://127.0.0.1:5173",
                "http://127.0.0.1:5173": "http://localhost:5173",
            }
            values = list(dict.fromkeys([*values, *(aliases[v] for v in values if v in aliases)]))
        return values
