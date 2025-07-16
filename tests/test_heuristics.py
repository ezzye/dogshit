import importlib
import yaml
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
