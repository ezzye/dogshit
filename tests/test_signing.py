import urllib.parse
from backend.signing import generate_signed_url, verify_signed_url


def _parse(url: str):
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(parsed.query)
    return parsed.path, int(q["expires"][0]), q["signature"][0]


def test_generate_and_verify():
    url = generate_signed_url("/download/1/summary", expires_in=60)
    path, expires, signature = _parse(url)
    assert verify_signed_url(path, expires, signature)


def test_expired_url():
    url = generate_signed_url("/download/1/summary", expires_in=-1)
    path, expires, signature = _parse(url)
    assert not verify_signed_url(path, expires, signature)


def test_tampered_url_fails():
    """Altering the path should invalidate the signature."""
    url = generate_signed_url("/download/1/summary", expires_in=60)
    path, expires, signature = _parse(url)
    # Tamper with the path after signing
    assert not verify_signed_url("/download/2/summary", expires, signature)
