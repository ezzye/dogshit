import pytest
from fastapi import HTTPException

from backend.auth import generate_token, validate_token, auth_dependency


def test_token_expiry():
    token = generate_token("auth", expires_in=-1)
    assert not validate_token(token, "auth")


def test_token_tamper_detection():
    token = generate_token("auth")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert not validate_token(tampered, "auth")


def test_auth_bypass(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    with pytest.raises(HTTPException):
        auth_dependency(token=None)
    monkeypatch.setenv("AUTH_BYPASS", "1")
    auth_dependency(token=None)  # should not raise
