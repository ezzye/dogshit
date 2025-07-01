from bankcleanr.llm import classify_transactions, PROVIDERS
from bankcleanr.transaction import Transaction
from bankcleanr.llm.openai import OpenAIAdapter

class DummyAdapter(OpenAIAdapter):
    def __init__(self, label="remote"):
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
