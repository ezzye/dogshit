import gzip
import json
import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.database import get_session


@pytest.fixture(name="client")
def client_fixture():
    os.environ["AUTH_BYPASS"] = "1"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)


def test_upload_and_status(client: TestClient):
    resp = client.post("/upload", data="hello")
    job_id = resp.json()["job_id"]
    status = client.get(f"/status/{job_id}").json()["status"]
    assert status == "pending"


def test_upload_gzip(client: TestClient):
    data = gzip.compress(b"foo")
    resp = client.post("/upload", data=data, headers={"Content-Encoding": "gzip"})
    assert "job_id" in resp.json()


def test_rules(client: TestClient):
    client.post("/rules", json={"rule_text": "allow"})
    rules = client.get("/rules").json()
    assert any(r["rule_text"] == "allow" for r in rules)


def test_classify(client: TestClient):
    job_id = client.post("/upload", data="data").json()["job_id"]
    resp = client.post("/classify", json={"job_id": job_id})
    assert "classification_id" in resp.json()


def test_download(client: TestClient):
    job_id = client.post("/upload", data="data").json()["job_id"]
    url = client.get(f"/download/{job_id}/summary").json()["url"]
    assert str(job_id) in url and "summary" in url
