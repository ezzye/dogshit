import importlib
import json
import urllib.request

import pytest
from sqlmodel import create_engine

from bankcleanr.rules import regex, db_store, heuristics
from bankcleanr.rules.manager import Manager
from bankcleanr.transaction import Transaction


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    db_file = tmp_path / "rules.db"
    importlib.reload(db_store)
    db_store.DB_PATH = db_file
    db_store.engine = create_engine(f"sqlite:///{db_file}", echo=False)
    db_store.init_db()
    importlib.reload(regex)
    regex.reload_patterns()
    importlib.reload(heuristics)
    yield


def test_classify_transactions():
    txs = [
        Transaction(date="2024-01-01", description="Spotify monthly", amount="-9.99"),
        Transaction(date="2024-01-02", description="Amazon Prime", amount="-8.99"),
        Transaction(date="2024-01-03", description="Dropbox subscription", amount="-11.99"),
        Transaction(date="2024-01-04", description="Coffee shop", amount="-2.50"),
    ]
    labels = heuristics.classify_transactions(txs)
    assert labels == ["spotify", "amazon prime", "dropbox", "unknown"]


def test_patterns_loaded_from_db():
    db_store.add_pattern("coffee", "coffee shop")
    regex.reload_patterns()
    importlib.reload(heuristics)

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    labels = heuristics.classify_transactions(txs)
    assert labels == ["coffee"]


def test_manager_persists_patterns():
    manager = Manager()
    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    manager.merge_llm_rules(txs, ["coffee"])
    manager.persist()
    assert db_store.get_patterns()["coffee"] == "Coffee shop"
    assert manager.classify(txs) == ["coffee"]


def test_manager_posts_backend(monkeypatch):
    posted = {}

    def fake_urlopen(req, timeout=0):
        posted["url"] = req.full_url
        posted["body"] = req.data.decode()
        class R:
            pass
        return R()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("BANKCLEANR_BACKEND_URL", "http://test")
    monkeypatch.setenv("BANKCLEANR_BACKEND_TOKEN", "tok")

    manager = Manager()
    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    manager.merge_llm_rules(txs, ["coffee"])
    manager.persist()

    assert posted["url"] == "http://test/heuristics?token=tok"
    assert json.loads(posted["body"]) == {"label": "coffee", "pattern": "Coffee shop"}
