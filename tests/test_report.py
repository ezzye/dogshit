import json
import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app import app
from backend.report import get_llm
from backend.database import get_session
from backend.models import LLMCost
from backend.llm_adapter import DailyCostTracker


class DummyHTML:
    def __init__(self, string: str):
        self.string = string

    def write_pdf(self, stylesheets=None):
        return b"%PDF-1.4\n%%EOF"


class DummyCSS:
    def __init__(self, string: str):
        self.string = string


@pytest.fixture(name="client")
def client_fixture(tmp_path: Path, monkeypatch):
    os.environ["AUTH_BYPASS"] = "1"
    os.environ["STORAGE_DIR"] = str(tmp_path)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    def dummy_llm(prompt: str):
        return "<html><body>Report</body></html>", {
            "prompt_tokens": 10,
            "completion_tokens": 5,
        }

    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    monkeypatch.setattr("backend.llm_adapter.get_session", get_session_override)
    dummy_weasy = types.SimpleNamespace(HTML=DummyHTML, CSS=DummyCSS)
    monkeypatch.setitem(sys.modules, "weasyprint", dummy_weasy)

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_llm] = lambda: dummy_llm

    with TestClient(app) as c:
        yield c, engine

    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


def _create_job(client: TestClient) -> int:
    resp = client.post("/upload", data="data", headers={"Content-Type": "text/plain"})
    return resp.json()["job_id"]


def test_report_generation(client: tuple[TestClient, any], tmp_path: Path):
    client_obj, engine = client
    job_id = _create_job(client_obj)
    summary = {
        "job_id": str(job_id),
        "user_id": "1",
        "period": {"start": "2024-01-01", "end": "2024-01-31"},
        "currency": "GBP",
        "totals": {"income": 0, "expenses": 0, "net": 0},
        "categories": [],
    }
    summary_path = Path(os.environ["STORAGE_DIR"]) / f"{job_id}_summary_v1.json"
    summary_path.write_text(json.dumps(summary))

    resp = client_obj.get(f"/report/{job_id}")
    assert resp.status_code == 200
    url = resp.json()["url"]

    download = client_obj.get(url)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"

    pdf_path = Path(os.environ["STORAGE_DIR"]) / f"{job_id}_report.pdf"
    assert pdf_path.exists()

    with Session(engine) as session:
        entries = list(session.exec(select(LLMCost)))
        assert len(entries) == 2
        llm_entry = next(e for e in entries if e.tokens_in == 10)
        pdf_entry = next(e for e in entries if e.tokens_in == 0)
        assert llm_entry.job_id == job_id
        assert pdf_entry.job_id == job_id
        assert llm_entry.tokens_out == 5
        assert pdf_entry.tokens_out == 0
        assert pdf_entry.estimated_cost_gbp > 0


def test_report_missing_summary(client: tuple[TestClient, any]):
    client_obj, _ = client
    job_id = _create_job(client_obj)
    resp = client_obj.get(f"/report/{job_id}")
    assert resp.status_code == 404
