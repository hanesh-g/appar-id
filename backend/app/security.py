import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pwdlib import PasswordHash

from .config import Settings
from .db import utcnow

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash(secrets.token_urlsafe(24))


class Crypto:
    def __init__(self, settings: Settings):
        self.aes = AESGCM(base64.b64decode(settings.pii_key.get_secret_value()))
        self.key = base64.b64decode(settings.hmac_key.get_secret_value())

    def encrypt(self, value: dict) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self.aes.encrypt(nonce, json.dumps(value, sort_keys=True).encode(), b"apaar:v1")

    def decrypt(self, value: bytes) -> dict:
        return json.loads(self.aes.decrypt(value[:12], value[12:], b"apaar:v1"))

    def digest(self, value: str) -> str:
        return hmac.new(self.key, value.encode(), hashlib.sha256).hexdigest()


def issue_token(user_id: str, settings: Settings) -> str:
    now = utcnow()
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
