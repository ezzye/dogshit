from bankcleanr.rules.heuristics import classify_transactions
from bankcleanr.transaction import Transaction


def test_classify_transactions():
    txs = [
        Transaction(date="2024-01-01", description="Spotify monthly", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.50"),
    ]
    labels = classify_transactions(txs)
    assert labels == ["spotify", "unknown"]
