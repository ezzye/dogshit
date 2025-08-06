import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from backend.app import app
from backend.report import get_llm
from backend.database import get_session


@pytest.fixture(name="client")
def client_fixture(tmp_path: Path, monkeypatch):
    os.environ["AUTH_BYPASS"] = "1"
    os.environ["STORAGE_DIR"] = str(tmp_path)

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    def dummy_llm(prompt: str) -> str:
        return "<html><body><h1>Report</h1></body></html>"

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_llm] = lambda: dummy_llm

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


def _create_job(client: TestClient) -> int:
    resp = client.post("/upload", data="data", headers={"Content-Type": "text/plain"})
    return resp.json()["job_id"]


def test_report_generation(client: TestClient, tmp_path: Path):
    job_id = _create_job(client)
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

    resp = client.get(f"/report/{job_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"

    pdf_path = Path(os.environ["STORAGE_DIR"]) / f"{job_id}_report.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size < 5 * 1024 * 1024


def test_report_missing_summary(client: TestClient):
    job_id = _create_job(client)
    resp = client.get(f"/report/{job_id}")
    assert resp.status_code == 404
