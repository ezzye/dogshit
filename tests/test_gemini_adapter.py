import builtins
import sys
from bankcleanr.llm.gemini import GeminiAdapter
from bankcleanr.transaction import Transaction


def test_returns_unknown_when_library_missing(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "google.generativeai":
            raise ImportError
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("google.generativeai", None)

    adapter = GeminiAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]


class DummyModels:
    def generate_content(self, *args, **kwargs):
        class Resp:
            text = '{"category": "coffee", "new_rule": ".*COFFEE.*"}'

        return Resp()


class DummyClient:
    models = DummyModels()


def test_classify_parses_json(monkeypatch):
    adapter = GeminiAdapter(api_key="dummy")
    adapter.client = DummyClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"


def test_retries_then_unknown():
    calls = {"n": 0}

    class FailingModels:
        def generate_content(self, *args, **kwargs):
            calls["n"] += 1
            raise RuntimeError("boom")

    class FailingClient:
        models = FailingModels()

    adapter = GeminiAdapter(api_key="dummy")
    adapter.client = FailingClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]
    assert calls["n"] == 3
