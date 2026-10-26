"""Add an audit-only key without replacing existing local secrets or data."""

import argparse
import base64
import os
import re
import secrets
import tempfile
from pathlib import Path

from dotenv import dotenv_values


def enable_audit(target: Path) -> None:
    if not target.is_file():
        raise ValueError("Initialise the local .env first")
    values = dotenv_values(target)
    if values.get("APP_ENV") not in {"local", "demo"}:
        raise ValueError("This helper is restricted to explicit local/demo configuration")
    key = values.get("AUDIT_HMAC_KEY")
    if key:
        try:
            if len(base64.b64decode(key, validate=True)) != 32:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(
                "Existing AUDIT_HMAC_KEY is invalid; its value is not printed or replaced"
            ) from None
    raw = target.read_text(encoding="utf-8")
    additions = {}
    if not key:
        additions["AUDIT_HMAC_KEY"] = base64.b64encode(secrets.token_bytes(32)).decode()
    if not values.get("AUDIT_KEY_ID"):
        additions["AUDIT_KEY_ID"] = "audit-v1"
    lines = []
    found_flag = False
    found_key = False
    for line in raw.splitlines(keepends=True):
        if re.match(r"^\s*AUDIT_CHAIN_ENABLED\s*=", line):
            lines.append('AUDIT_CHAIN_ENABLED="true"\n')
            found_flag = True
        elif re.match(r"^\s*AUDIT_HMAC_KEY\s*=", line) and not key:
            lines.append(f'AUDIT_HMAC_KEY="{additions.pop("AUDIT_HMAC_KEY")}"\n')
            found_key = True
        else:
            lines.append(line)
    text = "".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    if not found_flag:
        text += 'AUDIT_CHAIN_ENABLED="true"\n'
    if found_key:
        assert "AUDIT_HMAC_KEY" not in additions
    for name, value in additions.items():
        text += f'{name}="{value}"\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, prefix=".env.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        temporary.chmod(0o600)
        os.replace(temporary, target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-audit", action="store_true", required=True)
    parser.parse_args()
    try:
        enable_audit(Path(__file__).resolve().parents[1] / ".env")
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print("Audit integrity enabled in ignored .env. Existing keys preserved; no secret values printed.")
    print("Run migrations and restart the API. Keep the audit key across future restarts and deployments.")
