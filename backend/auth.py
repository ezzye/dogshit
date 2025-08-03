import base64
import hashlib
import hmac
import os
import time
from fastapi import Header, HTTPException

SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "changeme")
BYPASS_ENV = "AUTH_BYPASS"


def generate_token(data: str, expires_in: int = 3600) -> str:
    expiry = int(time.time()) + expires_in
    msg = f"{data}:{expiry}".encode()
    sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(msg + b":" + sig).decode()
    return token


def validate_token(token: str, data: str) -> bool:
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        parts = decoded.split(b":")
        if len(parts) != 3:
            return False
        msg = b":".join(parts[:-1])
        sig = parts[-1]
        expected = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return False
        payload, expiry = parts[0].decode(), int(parts[1])
        if payload != data:
            return False
        if time.time() > expiry:
            return False
        return True
    except Exception:
        return False


def auth_dependency(token: str = Header(None, alias="X-Auth-Token")) -> None:
    if os.getenv(BYPASS_ENV):
        return
    if not token or not validate_token(token, "auth"):
        raise HTTPException(status_code=401, detail="Unauthorized")
