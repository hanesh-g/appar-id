"""Enable optional demo extensions without replacing existing secrets or data."""

import argparse
import base64
import os
import re
import secrets
import tempfile
from pathlib import Path

from dotenv import dotenv_values


def enable_extension(target: Path, key_name: str, flag: str, key_id_name: str, key_id: str) -> None:
    if not target.is_file():
        raise ValueError("Initialise the local .env first")
    values = dotenv_values(target)
    if values.get("APP_ENV") not in {"local", "demo"}:
        raise ValueError("This helper is restricted to explicit local/demo configuration")
    key = values.get(key_name)
    if key:
        try:
            if len(base64.b64decode(key, validate=True)) != 32:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(
                f"Existing {key_name} is invalid; its value is not printed or replaced"
            ) from None
    raw = target.read_text(encoding="utf-8")
    additions = {}
    if not key:
        additions[key_name] = base64.b64encode(secrets.token_bytes(32)).decode()
    if not values.get(key_id_name):
        additions[key_id_name] = key_id
    lines = []
    found_flag = False
    found_key = False
    for line in raw.splitlines(keepends=True):
        if re.match(rf"^\s*{flag}\s*=", line):
            lines.append(f'{flag}="true"\n')
            found_flag = True
        elif re.match(rf"^\s*{key_name}\s*=", line) and not key:
            lines.append(f'{key_name}="{additions.pop(key_name)}"\n')
            found_key = True
        else:
            lines.append(line)
    text = "".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    if not found_flag:
        text += f'{flag}="true"\n'
    if found_key:
        assert key_name not in additions
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


def enable_audit(target: Path) -> None:
    enable_extension(target, "AUDIT_HMAC_KEY", "AUDIT_CHAIN_ENABLED", "AUDIT_KEY_ID", "audit-v1")


def enable_consent(target: Path) -> None:
    enable_extension(target, "GRANT_TOKEN_KEY", "CONSENT_ENABLED", "GRANT_KEY_ID", "grant-v1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enable-audit", action="store_true")
    parser.add_argument("--enable-consent", action="store_true")
    args = parser.parse_args()
    if not args.enable_audit and not args.enable_consent:
        parser.error("Select --enable-audit and/or --enable-consent")
    try:
        target = Path(__file__).resolve().parents[1] / ".env"
        if args.enable_audit:
            enable_audit(target)
        if args.enable_consent:
            enable_consent(target)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print("Selected extensions enabled in ignored .env. Existing keys preserved; no values printed.")
    print("Run migrations, seed demo accounts, and restart the API. Retain keys across restarts.")
