import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTES", "10080"))


class TokenDecodeError(Exception):
    pass


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(salt + digest).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        decoded = base64.b64decode(password_hash.encode("utf-8"))
    except Exception:
        return False

    if len(decoded) < 48:
        return False

    salt = decoded[:16]
    expected_digest = decoded[16:]
    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({"token_use": "access"})
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "jti": uuid4().hex})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({"token_use": "refresh"})
    expire = now + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "jti": uuid4().hex})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise TokenDecodeError("Invalid authentication token") from exc

    if payload.get("token_use") != "access":
        raise TokenDecodeError("Invalid authentication token")
    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise TokenDecodeError("Invalid refresh token") from exc

    if payload.get("token_use") != "refresh":
        raise TokenDecodeError("Invalid refresh token")
    return payload
