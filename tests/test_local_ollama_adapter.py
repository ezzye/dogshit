from bankcleanr.llm.local_ollama import LocalOllamaAdapter
from bankcleanr.transaction import Transaction
import requests


class DummyResp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def test_classify_parses_json(monkeypatch):
    def fake_post(*args, **kwargs):
        return DummyResp({"response": '{"category": "coffee", "new_rule": ".*COFFEE.*"}'})

    monkeypatch.setattr("bankcleanr.llm.local_ollama.requests.post", fake_post)
    adapter = LocalOllamaAdapter()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"


def test_retries_then_unknown(monkeypatch):
    calls = {"n": 0}

    def failing_post(*args, **kwargs):
        calls["n"] += 1
        raise requests.RequestException("boom")

    monkeypatch.setattr("bankcleanr.llm.local_ollama.requests.post", failing_post)
    adapter = LocalOllamaAdapter()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]
    assert calls["n"] == 3
