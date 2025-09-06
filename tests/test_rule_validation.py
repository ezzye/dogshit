import os
import sys
import types

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.database import get_session


@pytest.fixture(autouse=True)
def _mock_weasyprint(monkeypatch):
    if "weasyprint" not in sys.modules:
        monkeypatch.setitem(
            sys.modules, "weasyprint", types.SimpleNamespace(HTML=None, CSS=None)
        )


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


def test_create_rule_rejects_short_pattern(client: TestClient):
    resp = client.post("/rules", json={"user_id": 1, "label": "x", "pattern": "abcde"})
    assert resp.status_code == 400


def test_create_rule_rejects_narrower_field(client: TestClient):
    resp = client.post(
        "/rules",
        json={"user_id": 1, "label": "Groceries", "pattern": "coffeeshop", "field": "description"},
    )
    assert resp.status_code == 200
    resp = client.post(
        "/rules",
        json={
            "user_id": 1,
            "label": "Groceries",
            "pattern": "coffeeshop",
            "field": "merchant_signature",
        },
    )
    assert resp.status_code == 400
