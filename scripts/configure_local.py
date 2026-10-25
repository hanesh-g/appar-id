"""Create ignored local configuration without replacing any existing file."""
import argparse
import base64
import getpass
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--non-interactive", action="store_true")
args = parser.parse_args()
target = root / ".env"
if target.exists():
    raise SystemExit("Existing .env preserved. Edit it directly if changes are required.")
password = secrets.token_urlsafe(24)
demo = secrets.token_urlsafe(18) if args.non_interactive else getpass.getpass("Choose local demo login password (12+ characters): ")
if len(demo) < 12 or any(c in demo for c in ['\n', '\r', '"', "'"]):
    raise SystemExit("Use 12+ characters without quotes or newlines.")
values = {
    "APP_ENV": "local",
    "DATABASE_URL": f"postgresql+psycopg://apaar_app:{password}@localhost:5432/apaar",
    "TEST_DATABASE_URL": f"postgresql+psycopg://apaar_app:{password}@localhost:5432/apaar_test",
    "LOCAL_DB_PASSWORD": password,
    "JWT_SECRET": secrets.token_urlsafe(48),
    "PII_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
    "HMAC_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
    "JWT_ISSUER": "apaar-demo", "JWT_AUDIENCE": "apaar-web",
    "ALLOWED_ORIGINS": "http://localhost:5173",
    "REGISTRY_MODE": "mock", "MOCK_REGISTRY_OUTAGE": "false",
    "DEMO_PASSWORD": demo,
}
with target.open("x", encoding="utf-8") as file:
    for key, value in values.items():
        file.write(f'{key}="{value}"\n')
try:
    target.chmod(0o600)
except OSError:
    pass
print("Created ignored .env with generated keys. No secrets were printed.")
print("For non-interactive setup, choose DEMO_PASSWORD in your local .env before login.")
