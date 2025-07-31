import importlib
import contextlib
import json
from io import StringIO
import urllib.request

import pytest
from sqlmodel import create_engine

from bankcleanr.rules import regex, heuristics, db_store
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


def test_learn_new_patterns_prompts_once(monkeypatch):
    prompts: list[str] = []

    monkeypatch.setattr(regex, "classify", lambda d: "unknown")

    added: list[tuple[str, str]] = []
    monkeypatch.setattr(regex, "add_pattern", lambda label, p: added.append((label, p)))
    monkeypatch.setattr(regex, "reload_patterns", lambda: None)

    txs = [
        Transaction(date="2024-01-01", description="Coffee shop", amount="-1"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-1"),
    ]
    labels = ["coffee", "coffee"]

    out = StringIO()
    with contextlib.redirect_stdout(out):
        heuristics.learn_new_patterns(
            txs, labels, confirm=lambda prompt: prompts.append(prompt) or "y"
        )

    assert "Coffee shop (2)" in out.getvalue()
    assert prompts == ["Add pattern for 'coffee' matching 'Coffee shop'? [y/N] "]
    assert added == [("coffee", "Coffee shop")]


def test_learn_new_patterns_env(monkeypatch):
    monkeypatch.setattr(regex, "classify", lambda d: "unknown")
    monkeypatch.setattr(regex, "add_pattern", lambda label, p: (_ for _ in ()).throw(RuntimeError("should not add")))
    monkeypatch.setattr(regex, "reload_patterns", lambda: None)
    monkeypatch.setenv("BANKCLEANR_AUTO_CONFIRM", "")

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    labels = ["coffee"]

    heuristics.learn_new_patterns(txs, labels)


def test_group_unmatched_transactions(monkeypatch):
    monkeypatch.setattr(regex, "classify", lambda d: "unknown")

    txs = [
        Transaction(date="2024-01-01", description="Coffee shop", amount="-1"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-1"),
        Transaction(date="2024-01-03", description="Book store", amount="-1"),
    ]
    labels = ["coffee", "coffee", "books"]

    groups = heuristics.group_unmatched_transactions(txs, labels)
    assert groups == [
        ("coffee", "Coffee shop", 2),
        ("books", "Book store", 1),
    ]


def test_learn_new_patterns_posts_backend(monkeypatch):
    monkeypatch.setattr(regex, "classify", lambda d: "unknown")
    monkeypatch.setattr(regex, "add_pattern", lambda label, p: None)
    monkeypatch.setattr(regex, "reload_patterns", lambda: None)

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

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    heuristics.learn_new_patterns(txs, ["coffee"], confirm=lambda _: "y")

    assert posted["url"] == "http://test/heuristics?token=tok"
    assert json.loads(posted["body"]) == {"label": "coffee", "pattern": "Coffee shop"}
