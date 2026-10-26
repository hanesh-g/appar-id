import base64
import hashlib
import importlib.util

import pytest
from dotenv import dotenv_values

from app.config import ROOT, Settings

spec = importlib.util.spec_from_file_location(
    "configure_extensions", ROOT / "scripts" / "configure_extensions.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_local_audit_key_upgrade_preserves_existing_values_and_is_repeatable(tmp_path):
    target = tmp_path / ".env"
    target.write_text(
        'APP_ENV="local"\nPII_KEY="retained-test-marker"\nHMAC_KEY="retained-lookup-marker"\nJWT_SECRET="retained-session-marker"\nAUDIT_CHAIN_ENABLED=false\n'
    )
    module.enable_audit(target)
    values = dotenv_values(target)
    assert values["PII_KEY"] == "retained-test-marker"
    assert values["HMAC_KEY"] == "retained-lookup-marker"
    assert values["JWT_SECRET"] == "retained-session-marker"
    decoded_length = len(base64.b64decode(values["AUDIT_HMAC_KEY"], validate=True))
    assert decoded_length == 32 and values["AUDIT_CHAIN_ENABLED"] == "true"
    before = hashlib.sha256(target.read_bytes()).digest()
    module.enable_audit(target)
    assert hashlib.sha256(target.read_bytes()).digest() == before


def test_key_upgrade_refuses_non_demo_configuration(tmp_path):
    target = tmp_path / ".env"
    target.write_text('APP_ENV="production"\n')
    before = hashlib.sha256(target.read_bytes()).digest()
    with pytest.raises(ValueError):
        module.enable_audit(target)
    assert hashlib.sha256(target.read_bytes()).digest() == before


def test_consent_key_is_separate_repeatable_and_preserves_audit_key(tmp_path):
    target = tmp_path / ".env"
    target.write_text('APP_ENV="demo"\n')
    module.enable_audit(target)
    audit = dotenv_values(target)["AUDIT_HMAC_KEY"]
    module.enable_consent(target)
    values = dotenv_values(target)
    assert values["CONSENT_ENABLED"] == "true" and values["AUDIT_HMAC_KEY"] == audit
    assert len(base64.b64decode(values["GRANT_TOKEN_KEY"], validate=True)) == 32
    assert values["GRANT_TOKEN_KEY"] != audit
    before = target.read_bytes()
    module.enable_consent(target)
    assert target.read_bytes() == before


def test_extension_keys_cannot_reuse_the_identity_lookup_key():
    settings = Settings()
    with pytest.raises(ValueError, match="must be distinct"):
        Settings(audit_hmac_key=settings.hmac_key)
