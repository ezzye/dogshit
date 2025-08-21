import json
import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from backend.app import app, get_adapter_dependency
from backend.llm_adapter import AbstractAdapter
from backend.database import get_session


@pytest.fixture(autouse=True)
def _mock_weasyprint(monkeypatch):
    if "weasyprint" not in sys.modules:
        monkeypatch.setitem(
            sys.modules, "weasyprint", types.SimpleNamespace(HTML=None, CSS=None)
        )


@pytest.fixture
def client(monkeypatch):
    os.environ["AUTH_BYPASS"] = "1"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    class DummyAdapter(AbstractAdapter):
        def __init__(self):
            super().__init__("test")
            self.calls = 0

        def _send(self, prompts):
            self.calls += 1
            return {"labels": [("unknown", 0.0)] * len(prompts), "usage": {"total_tokens": 0}}

    dummy_adapter = DummyAdapter()

    def adapter_override():
        return dummy_adapter

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_adapter_dependency] = adapter_override
    monkeypatch.setattr("backend.llm_adapter.get_session", get_session_override)
    with TestClient(app) as c:
        c.adapter = dummy_adapter
        c.engine = engine
        yield c
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)
    from backend import app as app_module
    app_module.SIGNATURE_CACHE.clear()


def test_classify_writes_summary_files(client: TestClient, tmp_path: Path):
    os.environ["STORAGE_DIR"] = str(tmp_path)
    content = "\n".join(
        [
            json.dumps(
                {
                    "date": "2024-01-01",
                    "amount": "10",
                    "description": "coffee",
                    "type": "debit",
                }
            ),
            json.dumps(
                {
                    "date": "2024-01-02",
                    "amount": "5",
                    "description": "salary",
                    "type": "credit",
                }
            ),
        ]
    )
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]
    resp = client.post("/classify", json={"job_id": job_id})
    assert resp.status_code == 200
    assert (tmp_path / f"{job_id}_summary_v1.json").exists()
    assert (tmp_path / f"{job_id}_summary.csv").exists()
