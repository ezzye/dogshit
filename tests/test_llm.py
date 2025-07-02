from bankcleanr.llm import classify_transactions, PROVIDERS
from bankcleanr.transaction import Transaction
from bankcleanr.llm.openai import OpenAIAdapter
from bankcleanr.settings import Settings
from pathlib import Path

class DummyAdapter(OpenAIAdapter):
    def __init__(self, label="remote", **kwargs):
        self.label = label

    def classify_transactions(self, transactions):
        return [self.label for _ in transactions]


def test_llm_fallback(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "openai", DummyAdapter)
    txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]
    labels = classify_transactions(txs, provider="openai")
    assert labels == ["spotify", "remote"]


def test_get_adapter_passes_api_key(monkeypatch):
    captured = {}

    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "openai", CaptureAdapter)
    settings = Settings(llm_provider="openai", api_key="secret", config_path=Path("cfg"))
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: settings)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "secret"


def test_llm_masks_before_sending(monkeypatch):
    captured = {}

    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            pass

        def classify_transactions(self, transactions):
            captured["descriptions"] = [tx.description for tx in transactions]
            return ["remote"]

    monkeypatch.setitem(PROVIDERS, "openai", CaptureAdapter)
    txs = [Transaction(date="2024-01-01", description="Send 12-34-56 12345678", amount="-9.99")]
    classify_transactions(txs, provider="openai")
    assert captured["descriptions"][0] == "Send ****3456 ****5678"
