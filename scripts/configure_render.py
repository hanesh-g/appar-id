"""Generate private settings for a fresh hosted synthetic demo, without touching local settings."""

import base64
import os
import secrets
from pathlib import Path


def create_settings(project_root: Path) -> Path:
    target = project_root / ".env.render"
    values = {
        "PYTHON_VERSION": "3.12.14",
        "APP_ENV": "demo",
        "DATABASE_URL": "REPLACE_WITH_RENDER_INTERNAL_DATABASE_URL",
        "ALLOWED_ORIGINS": "https://replace-with-your-project.vercel.app",
        "REGISTRY_MODE": "mock",
        "MOCK_REGISTRY_OUTAGE": "false",
        "AUDIT_CHAIN_ENABLED": "true",
        "AUDIT_KEY_ID": "audit-v1",
        "CONSENT_ENABLED": "true",
        "GRANT_KEY_ID": "grant-v1",
        "JWT_SECRET": secrets.token_urlsafe(48),
        "JWT_ISSUER": "apaar-demo",
        "JWT_AUDIENCE": "apaar-web",
        "PII_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "HMAC_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "AUDIT_HMAC_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "GRANT_TOKEN_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "DEMO_PASSWORD": secrets.token_urlsafe(24),
    }
    # Exclusive creation preserves the first generated keys across later runs.
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
        output.write(
            "# Private Render settings for a fresh synthetic demo. Never commit or publish this file.\n"
        )
        output.write("# Keep these keys for every redeploy of this database.\n")
        output.write("\n".join(f"{name}={value}" for name, value in values.items()) + "\n")
    return target


if __name__ == "__main__":
    try:
        create_settings(Path(__file__).resolve().parents[1])
    except FileExistsError:
        print("Existing .env.render preserved. Reuse its keys; do not regenerate them.")
    else:
        print("Created ignored .env.render with generated secrets. No secrets were printed.")
    print(
        "Edit DATABASE_URL privately, import the settings into Render, and set the final Vercel origin later."
    )
