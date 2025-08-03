import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

SECRET_KEY = os.environ.get("SIGNING_SECRET_KEY", "changeme")


def generate_signed_url(path: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for the given path.

    Args:
        path: The path portion of the URL beginning with '/'.
        expires_in: Seconds until expiration.

    Returns:
        The path with appended query parameters "expires" and "signature".
    """
    expiry = int(time.time()) + expires_in
    msg = f"{path}:{expiry}".encode()
    signature = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
    query = urlencode({"expires": expiry, "signature": signature})
    return f"{path}?{query}"


def verify_signed_url(path: str, expires: int, signature: str) -> bool:
    """Verify a signed URL."""
    msg = f"{path}:{expires}".encode()
    expected = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    if time.time() > int(expires):
        return False
    return True
