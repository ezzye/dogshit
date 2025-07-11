from decimal import Decimal
from bankcleanr.transaction import Transaction
from bankcleanr.recommendation import Recommendation
from bankcleanr.analytics import calculate_savings, totals_by_type, summarize_by_description


def test_calculate_savings():
    recs = [
        Recommendation(Transaction(date="2024-01-01", description="Spotify", amount="-9.99"), "spotify", "Cancel"),
        Recommendation(Transaction(date="2024-01-02", description="Coffee", amount="-2.00"), "coffee", "Keep"),
    ]
    assert calculate_savings(recs) == Decimal("9.99")


def test_totals_by_type():
    recs = [
        Recommendation(Transaction(date="2024-01-01", description="Spotify", amount="-9.99"), "spotify", "Cancel"),
        Recommendation(Transaction(date="2024-01-02", description="Dropbox", amount="-5.00"), "dropbox", "Cancel"),
        Recommendation(Transaction(date="2024-01-03", description="Bus", amount="-2.50"), "bus", "Keep"),
    ]
    totals = totals_by_type(recs)
    assert totals["entertainment"] == Decimal("9.99")
    assert totals["cloud"] == Decimal("5.00")
    assert totals["other"] == Decimal("2.50")


def test_summarize_by_description():
    txs = [
        Transaction(date="2024-01-01", description="Coffee", amount="-2.00"),
        Transaction(date="2024-01-02", description="Coffee", amount="-1.50"),
        Transaction(date="2024-01-03", description="Groceries", amount="-5.00"),
        Transaction(date="2024-01-04", description="Coffee", amount="1.00"),
    ]
    totals = summarize_by_description(txs)
    assert totals["Coffee"] == Decimal("4.50")
    assert totals["Groceries"] == Decimal("5.00")
