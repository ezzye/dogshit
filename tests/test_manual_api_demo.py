"""Tests for the manual API demo script."""

from __future__ import annotations

import types
from scripts import manual_api_demo


class DummyResponse:
    def __init__(self, json_data=None, text: str = "", content: bytes = b"") -> None:
        self._json = json_data or {}
        self.text = text
        self.content = content

    def raise_for_status(self) -> None:  # pragma: no cover - always success
        return

    def json(self):  # noqa: D401 - mimic requests.Response
        return self._json


def test_manual_api_demo_includes_auth_header(monkeypatch, tmp_path):
    """Ensure the demo adds the auth header when calling the API."""

    calls = {"post": [], "get": []}

    def fake_post(url, data=None, json=None, headers=None):
        calls["post"].append({"url": url, "headers": headers})
        if url.endswith("/upload"):
            return DummyResponse({"job_id": 1})
        if url.endswith("/classify"):
            return DummyResponse()
        return DummyResponse()

    def fake_get(url, headers=None):
        calls["get"].append({"url": url, "headers": headers})
        if url.endswith("/report/1"):
            return DummyResponse({"url": "/download/1/report"})
        if "summary" in url:
            return DummyResponse(text="{}")
        if "download/1/report" in url:
            return DummyResponse(content=b"pdf")
        return DummyResponse()

    monkeypatch.setattr(
        manual_api_demo, "requests", types.SimpleNamespace(post=fake_post, get=fake_get)
    )

    report_path = tmp_path / "report.pdf"
    monkeypatch.setattr(manual_api_demo, "Path", lambda name: report_path)

    manual_api_demo.main()

    upload_headers = calls["post"][0]["headers"]
    assert upload_headers and "X-Auth-Token" in upload_headers
    assert report_path.exists()

