from pathlib import Path
import json
import sys
import jsonschema
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.analytics import (
    compute_monthly_totals,
    detect_recurring,
    detect_overspending,
    generate_summary,
    SCHEMA_PATH,
)


def test_compute_monthly_totals():
    transactions = [
        {"date": "2024-01-10", "amount": "10", "merchant_signature": "a", "type": "credit"},
        {"date": "2024-01-15", "amount": "5", "merchant_signature": "b", "type": "debit"},
        {"date": "2024-02-01", "amount": "3", "merchant_signature": "c", "type": "credit"},
    ]
    totals = compute_monthly_totals(transactions)
    assert totals == {"2024-01": 5.0, "2024-02": 3.0}


def test_detect_recurring():
    transactions = [
        {"date": "2024-01-01", "amount": "10", "merchant_signature": "netflix", "type": "debit"},
        {"date": "2024-02-01", "amount": "10", "merchant_signature": "netflix", "type": "debit"},
        {"date": "2024-03-01", "amount": "10", "merchant_signature": "netflix", "type": "debit"},
    ]
    recurring = detect_recurring(transactions)
    assert recurring and recurring[0]["merchant"] == "netflix"
    assert recurring[0]["cadence"] == "monthly"
    assert recurring[0]["count"] == 3


def test_detect_overspending(tmp_path: Path):
    transactions = [
        {"date": "2024-01-10", "amount": "50", "merchant_signature": "grocer1", "category": "Groceries", "type": "debit"},
        {"date": "2024-02-10", "amount": "50", "merchant_signature": "grocer1", "category": "Groceries", "type": "debit"},
        {"date": "2024-03-10", "amount": "150", "merchant_signature": "grocer1", "category": "Groceries", "type": "debit"},
        {"date": "2024-01-05", "amount": "5", "merchant_signature": "coffee", "category": "Groceries", "type": "debit"},
        {"date": "2024-02-05", "amount": "5", "merchant_signature": "coffee", "category": "Groceries", "type": "debit"},
        {"date": "2024-03-05", "amount": "20", "merchant_signature": "coffee", "category": "Groceries", "type": "debit"},
        {"date": "2024-01-01", "amount": "10", "merchant_signature": "netflix", "category": "Subscriptions", "type": "debit"},
        {"date": "2024-02-01", "amount": "10", "merchant_signature": "netflix", "category": "Subscriptions", "type": "debit"},
        {"date": "2024-03-01", "amount": "12", "merchant_signature": "netflix", "category": "Subscriptions", "type": "debit"},
    ]

    recurring = detect_recurring(transactions)
    highlights = detect_overspending(transactions, recurring)

    assert any("Groceries" in h for h in highlights)
    assert any("coffee" in h for h in highlights)
    assert any("netflix" in h for h in highlights)

    # also ensure summary generation validates against schema
    summary = generate_summary(
        transactions,
        job_id="00000000-0000-0000-0000-000000000000",
        user_id="user",
        period={"start": "2024-01-01", "end": "2024-03-31"},
        output_dir=tmp_path,
    )
    with open("schemas/summary_v1.json") as f:
        schema = json.load(f)
    jsonschema.validate(summary, schema)
    assert (tmp_path / "summary_v1.json").exists()
    assert (tmp_path / "summary.csv").exists()


def test_generate_summary_missing_schema(tmp_path: Path):
    transactions = [
        {"date": "2024-01-10", "amount": "10", "merchant_signature": "a", "type": "credit"}
    ]
    backup = SCHEMA_PATH.with_suffix(".bak")
    SCHEMA_PATH.rename(backup)
    try:
        with pytest.raises(FileNotFoundError):
            generate_summary(
                transactions,
                job_id="00000000-0000-0000-0000-000000000000",
                user_id="user",
                period={"start": "2024-01-01", "end": "2024-01-31"},
                output_dir=tmp_path,
            )
    finally:
        backup.rename(SCHEMA_PATH)
