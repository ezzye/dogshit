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
