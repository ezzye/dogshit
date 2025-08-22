import gzip
import os
import json
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from backend.app import app, get_adapter_dependency
from backend.llm_adapter import AbstractAdapter, _adapter_instances
from backend.database import get_session
from backend.signing import generate_signed_url
from backend.models import LLMCost, UserRule


@pytest.fixture(autouse=True)
def _mock_weasyprint(monkeypatch):
    if "weasyprint" not in sys.modules:
        monkeypatch.setitem(
            sys.modules, "weasyprint", types.SimpleNamespace(HTML=None, CSS=None)
        )


@pytest.fixture(name="client")
def client_fixture(monkeypatch):
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


def test_upload_and_status(client: TestClient):
    resp = client.post(
        "/upload",
        files={"file": ("test.jsonl", "hello", "text/plain")},
    )
    job_id = resp.json()["job_id"]
    status = client.get(f"/status/{job_id}").json()["status"]
    assert status == "uploaded"


def test_upload_gzip(client: TestClient):
    data = gzip.compress(b"foo")
    resp = client.post(
        "/upload",
        data=data,
        headers={"Content-Encoding": "gzip", "Content-Type": "text/plain"},
    )
    assert "job_id" in resp.json()


def test_rules(client: TestClient):
    client.post("/rules", json={"label": "Groceries", "pattern": "allowed"})
    rules = client.get("/rules").json()
    assert any(r["label"] == "Groceries" for r in rules)


def test_rule_rejects_unknown_label(client: TestClient):
    resp = client.post("/rules", json={"label": "UnknownLabel", "pattern": "allowed"})
    assert resp.status_code == 400


def test_rule_rejects_short_pattern(client: TestClient):
    resp = client.post("/rules", json={"label": "Groceries", "pattern": "abc"})
    assert resp.status_code == 400


def test_rule_rejects_pattern_with_digits(client: TestClient):
    """Digits and symbols should not count toward the minimum pattern length."""
    resp = client.post(
        "/rules", json={"label": "Groceries", "pattern": "ab12cd"}
    )
    assert resp.status_code == 400


def test_rule_normalises_pattern(client: TestClient):
    resp = client.post(
        "/rules", json={"label": "Groceries", "pattern": "Coffee-Shop!"}
    )
    assert resp.status_code == 200
    assert resp.json()["pattern"] == "coffeeshop"


def test_rule_overwrites_higher_confidence(client: TestClient):
    low = client.post(
        "/rules",
        json={
            "label": "Groceries",
            "pattern": "coffee shop",
            "confidence": 0.5,
            "provenance": "llm",
        },
    ).json()
    assert low["version"] == 1
    high = client.post(
        "/rules",
        json={
            "label": "Groceries",
            "pattern": "coffee shop",
            "confidence": 0.9,
            "provenance": "llm",
        },
    ).json()
    assert high["version"] == 2
    assert high["confidence"] == 0.9
    assert high["provenance"] == "llm"


def test_classify(client: TestClient):
    content = "\n".join(
        [
            json.dumps({"description": "data", "type": "debit"}),
            json.dumps({"description": "other", "type": "debit"}),
        ]
    )
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]
    resp = client.post("/classify", json={"job_id": job_id})
    data = resp.json()["transactions"]
    labels = [r["label"] for r in data]
    assert labels == ["unknown", "unknown"]
    categories = [r["category"] for r in data]
    assert categories == ["unknown", "unknown"]
    assert all(r["type"] == "debit" for r in data)
    # ensure the job status is updated once processing is complete
    status = client.get(f"/status/{job_id}").json()["status"]
    assert status == "completed"


def test_classify_missing_api_key(client: TestClient, monkeypatch):
    app.dependency_overrides.pop(get_adapter_dependency, None)
    _adapter_instances.clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resp = client.post("/classify", json={"job_id": 1})
    assert resp.status_code == 400
    assert "OPENAI_API_KEY not set" in resp.json()["detail"]


def test_summary_endpoints(client: TestClient, tmp_path: Path):
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
    client.post("/classify", json={"job_id": job_id})
    resp = client.get(f"/summary/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    generated_at = data.pop("generated_at")
    assert isinstance(generated_at, str)
    assert data == {
        "job_id": str(job_id),
        "user_id": "0",
        "period": {"start": "2024-01-01", "end": "2024-01-02"},
        "currency": "GBP",
        "totals": {"income": 5.0, "expenses": -10.0, "net": -5.0},
        "categories": [
            {
                "name": "Groceries",
                "total": -10.0,
                "count": 1,
                "sample_merchants": ["coffee"],
            }
        ],
        "recurring": [],
        "highlights": {"overspending": [], "anomalies": []},
    }
    # regenerate via POST
    (tmp_path / f"{job_id}_summary_v1.json").unlink()
    (tmp_path / f"{job_id}_summary.csv").unlink()
    resp = client.post("/summary", json={"job_id": job_id})
    assert resp.status_code == 200
    assert (tmp_path / f"{job_id}_summary_v1.json").exists()


def test_classify_applies_user_rule(client: TestClient):
    content = "\n".join(
        [
            json.dumps({"description": "coffee shop", "type": "debit"}),
            json.dumps({"description": "mystery", "type": "debit"}),
        ]
    )
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]
    client.post(
        "/rules",
        json={"user_id": 1, "label": "coffee", "pattern": "coffee", "priority": 5},
    )
    resp = client.post("/classify", json={"job_id": job_id, "user_id": 1})
    labels = [r["label"] for r in resp.json()["transactions"]]
    assert labels == ["coffee", "unknown"]


def test_transactions_endpoint_filters(client: TestClient):
    content = "\n".join(
        [
            json.dumps({"description": "alpha", "type": "debit"}),
            json.dumps({"description": "coffee", "type": "debit"}),
        ]
    )
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]
    client.post("/rules", json={"label": "coffee", "pattern": "coffee"})
    client.post("/classify", json={"job_id": job_id})
    all_txs = client.get(f"/transactions/{job_id}").json()
    assert len(all_txs) == 2
    filtered_desc = client.get(
        f"/transactions/{job_id}", params={"description": "alpha"}
    ).json()
    assert len(filtered_desc) == 1
    assert filtered_desc[0]["description"] == "alpha"
    filtered_type_rule = client.get(
        f"/transactions/{job_id}", params={"type": "rule"}
    ).json()
    assert len(filtered_type_rule) == 1
    assert filtered_type_rule[0]["description"] == "coffee"
    filtered_both = client.get(
        f"/transactions/{job_id}", params={"type": "rule", "description": "coffee"}
    ).json()
    assert len(filtered_both) == 1
    assert filtered_both[0]["description"] == "coffee"


def test_classify_uses_cache(client: TestClient):
    content = "\n".join(
        [
            json.dumps({"description": "mystery shop 123", "type": "debit"}),
            json.dumps({"description": "mystery shop 123", "type": "debit"}),
        ]
    )
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]
    client.post("/classify", json={"job_id": job_id})
    client.post("/classify", json={"job_id": job_id})
    assert client.adapter.calls == 1


def test_classify_learns_user_rule_and_reuses(client: TestClient):
    class LearningAdapter(AbstractAdapter):
        def __init__(self):
            super().__init__("test")
            self.calls = 0

        def _send(self, prompts):
            self.calls += 1
            return {"labels": [("Groceries", 0.9) for _ in prompts], "usage": {"total_tokens": 0}}

    adapter = LearningAdapter()
    app.dependency_overrides[get_adapter_dependency] = lambda: adapter
    client.adapter = adapter

    content = json.dumps({"description": "Mystery Shop", "type": "debit"})
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]

    resp1 = client.post("/classify", json={"job_id": job_id, "user_id": 1})
    tx1 = resp1.json()["transactions"][0]
    assert tx1["classification_type"] == "llm"
    assert adapter.calls == 1
    with Session(client.engine) as session:
        rule = session.exec(select(UserRule)).one()
        assert rule.provenance == "llm"
        assert rule.version == 1
        label = rule.label

    from backend import app as app_module

    app_module.SIGNATURE_CACHE.clear()
    resp2 = client.post("/classify", json={"job_id": job_id, "user_id": 1})
    tx2 = resp2.json()["transactions"][0]
    assert tx2["classification_type"] == "rule"
    assert tx2["label"] == label
    assert adapter.calls == 1


def test_classify_overwrites_higher_confidence_rule(
    client: TestClient, monkeypatch
):
    class SeqAdapter(AbstractAdapter):
        def __init__(self):
            super().__init__("test")
            self.responses = [
                {"label": "Groceries", "confidence": 0.9},
                {"label": "Groceries", "confidence": 0.99},
            ]
            self.calls = 0

        def _send(self, prompts):
            resp = self.responses[self.calls]
            self.calls += 1
            return {
                "labels": [(resp["label"], resp["confidence"]) for _ in prompts],
                "usage": {"total_tokens": 0},
            }

    adapter = SeqAdapter()
    app.dependency_overrides[get_adapter_dependency] = lambda: adapter
    monkeypatch.setattr("backend.app.evaluate", lambda *args, **kwargs: None)

    content = json.dumps({"description": "Coffee Shop", "type": "debit"})
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]

    client.post("/classify", json={"job_id": job_id, "user_id": 1})
    with Session(client.engine) as session:
        rule = session.exec(select(UserRule)).one()
        assert rule.confidence == pytest.approx(0.9)
        assert rule.version == 1

    from backend import app as app_module

    app_module.SIGNATURE_CACHE.clear()
    client.post("/classify", json={"job_id": job_id, "user_id": 1})
    with Session(client.engine) as session:
        rule = session.exec(select(UserRule)).one()
        assert rule.confidence == pytest.approx(0.99)
        assert rule.version == 2
        assert rule.provenance == "llm"


def test_classify_rejects_off_taxonomy_label(client: TestClient):
    class OffTaxonomyAdapter(AbstractAdapter):
        def __init__(self):
            super().__init__("test")

        def _send(self, prompts):
            return {
                "labels": [("NonExistingCategory", 0.99) for _ in prompts],
                "usage": {"total_tokens": 0},
            }

    adapter = OffTaxonomyAdapter()
    app.dependency_overrides[get_adapter_dependency] = lambda: adapter
    client.adapter = adapter

    content = json.dumps({"description": "Mystery Shop", "type": "debit"})
    job_id = client.post(
        "/upload",
        data=content,
        headers={"Content-Type": "application/x-ndjson"},
    ).json()["job_id"]

    resp = client.post("/classify", json={"job_id": job_id, "user_id": 1})
    tx = resp.json()["transactions"][0]
    assert tx["label"] == "unknown"
    assert tx["classification_type"] == "unknown"

    with Session(client.engine) as session:
        rules = session.exec(select(UserRule)).all()
        assert rules == []


def test_costs_endpoint_aggregates_entries(client: TestClient):
    """Costs endpoint should sum multiple LLMCost rows for a job."""
    job_id = client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    ).json()["job_id"]
    with Session(client.engine) as session:
        session.add(
            LLMCost(
                job_id=job_id,
                tokens_in=10,
                tokens_out=5,
                estimated_cost_gbp=0.01,
            )
        )
        session.add(
            LLMCost(
                job_id=job_id,
                tokens_in=20,
                tokens_out=15,
                estimated_cost_gbp=0.03,
            )
        )
        session.commit()

    resp = client.get(f"/costs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tokens_in"] == 30
    assert data["tokens_out"] == 20
    assert data["total_tokens"] == 50
    assert data["estimated_cost_gbp"] == pytest.approx(0.04)

def test_download(client: TestClient, tmp_path: Path):
    job_id = client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    ).json()["job_id"]
    os.environ["STORAGE_DIR"] = str(tmp_path)
    file_path = tmp_path / f"{job_id}_summary.txt"
    file_path.write_text("result")
    url = generate_signed_url(f"/download/{job_id}/summary", expires_in=60)
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.content == b"result"


def test_download_tampered(client: TestClient, tmp_path: Path):
    job_id = client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    ).json()["job_id"]
    os.environ["STORAGE_DIR"] = str(tmp_path)
    file_path = tmp_path / f"{job_id}_summary.txt"
    file_path.write_text("result")
    url = generate_signed_url(f"/download/{job_id}/summary", expires_in=60)
    from urllib.parse import urlparse, parse_qs, urlencode

    parts = urlparse(url)
    params = parse_qs(parts.query)
    params["signature"] = ["0" * 64]
    tampered = f"{parts.path}?{urlencode({k: v[0] for k, v in params.items()})}"
    resp = client.get(tampered)
    assert resp.status_code == 403


def test_download_expired(client: TestClient, tmp_path: Path):
    job_id = client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    ).json()["job_id"]
    os.environ["STORAGE_DIR"] = str(tmp_path)
    file_path = tmp_path / f"{job_id}_summary.txt"
    file_path.write_text("result")
    url = generate_signed_url(f"/download/{job_id}/summary", expires_in=-1)
    resp = client.get(url)
    assert resp.status_code == 403


def test_upload_rejects_invalid_content_type(client: TestClient):
    resp = client.post(
        "/upload", data="data", headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 415


def test_upload_rejects_large_payload(client: TestClient):
    data = b"x" * (100 * 1024 * 1024 + 1)
    resp = client.post(
        "/upload", data=data, headers={"Content-Type": "text/plain"}
    )
    assert resp.status_code == 413
