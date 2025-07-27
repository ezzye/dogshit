import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app
from backend.db import get_session, init_db
from backend.models import User
from sqlmodel import select, create_engine

@pytest.fixture(autouse=True)
def _set_env(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    # ensure fresh db file per test
    db_file = tmp_path / "test.db"
    monkeypatch.setitem(os.environ, "APP_ENV", "test")
    from importlib import reload
    import backend.db as db
    reload(db)
    db.DB_PATH = db_file
    db.engine = create_engine(f"sqlite:///{db_file}", echo=False)
    init_db()
    yield
    db_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_upload_and_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/auth/request", params={"email": "u@test"})
        with get_session() as s:
            user = s.exec(select(User).where(User.email == "u@test")).first()
            token = user.token
        await client.post("/auth/verify", params={"token": token})
        txs = [
            {"date": "2024-01-01", "description": "Coffee", "amount": "-1"},
            {"date": "2024-01-02", "description": "Bus", "amount": "-2"},
        ]
        resp = await client.post("/upload", json=txs, params={"token": token})
        assert resp.status_code == 200
        resp = await client.get("/summary", params={"token": token})
        assert resp.json()["transactions"] == 2


@pytest.mark.asyncio
async def test_add_heuristic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/auth/request", params={"email": "u@test"})
        with get_session() as s:
            user = s.exec(select(User).where(User.email == "u@test")).first()
            token = user.token
        await client.post("/auth/verify", params={"token": token})
        payload = {"label": "coffee", "pattern": "Coffee shop"}
        resp = await client.post("/heuristics", json=payload, params={"token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] == "coffee"
        assert data["pattern"] == "Coffee shop"


@pytest.mark.asyncio
async def test_heuristic_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/auth/request", params={"email": "u@test"})
        with get_session() as s:
            user = s.exec(select(User).where(User.email == "u@test")).first()
            token = user.token
        await client.post("/auth/verify", params={"token": token})

        # initially empty
        resp = await client.get("/heuristics", params={"token": token})
        assert resp.status_code == 200
        assert resp.json() == []

        payload = {"label": "coffee", "pattern": "Coffee shop"}
        resp = await client.post("/heuristics", json=payload, params={"token": token})
        assert resp.status_code == 200
        rule_id = resp.json()["id"]

        resp = await client.get("/heuristics", params={"token": token})
        assert len(resp.json()) == 1

        resp = await client.delete(f"/heuristics/{rule_id}", params={"token": token})
        assert resp.status_code == 200

        resp = await client.get("/heuristics", params={"token": token})
        assert resp.json() == []
