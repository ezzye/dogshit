import importlib
import yaml
from io import StringIO
import contextlib
from bankcleanr.rules import regex
from bankcleanr.rules import heuristics
from bankcleanr.transaction import Transaction


def test_classify_transactions():
    txs = [
        Transaction(date="2024-01-01", description="Spotify monthly", amount="-9.99"),
        Transaction(date="2024-01-02", description="Amazon Prime", amount="-8.99"),
        Transaction(date="2024-01-03", description="Dropbox subscription", amount="-11.99"),
        Transaction(date="2024-01-04", description="Coffee shop", amount="-2.50"),
    ]
    labels = heuristics.classify_transactions(txs)
    assert labels == ["spotify", "amazon prime", "dropbox", "unknown"]


def test_patterns_loaded_from_yaml(tmp_path, monkeypatch):
    data = {"coffee": "coffee shop"}
    path = tmp_path / "heuristics.yml"
    path.write_text(yaml.safe_dump(data))

    importlib.reload(regex)
    monkeypatch.setattr(regex, "HEURISTICS_PATH", path, raising=False)
    regex.reload_patterns(path)
    importlib.reload(heuristics)

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    labels = heuristics.classify_transactions(txs)
    assert labels == ["coffee"]

    # restore default patterns
    importlib.reload(regex)
    importlib.reload(heuristics)


def test_learn_new_patterns_prompts_once(monkeypatch):
    prompts: list[str] = []

    monkeypatch.setattr(regex, "classify", lambda d: "unknown")

    added: list[tuple[str, str]] = []
    monkeypatch.setattr(regex, "add_pattern", lambda l, p: added.append((l, p)))
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
    monkeypatch.setattr(regex, "add_pattern", lambda l, p: (_ for _ in ()).throw(RuntimeError("should not add")))
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
