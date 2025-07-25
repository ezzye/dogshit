import csv
import pytest
import pdfplumber
from bankcleanr.recommendation import Recommendation
from bankcleanr.transaction import Transaction

from bankcleanr.io.loader import load_transactions
from bankcleanr.reports.writer import (
    write_summary,
    write_pdf_summary,
    format_terminal_summary,
)
from bankcleanr.reports.disclaimers import GLOBAL_DISCLAIMER


def test_load_transactions_pdf_dispatch(monkeypatch):
    called = {}

    def fake_parse(path):
        called["path"] = path
        return [{"a": 1}]

    monkeypatch.setattr("bankcleanr.io.pdf.generic.parse_pdf", fake_parse)
    result = load_transactions("statement.pdf")
    assert result == [{"a": 1}]
    assert called["path"] == "statement.pdf"


def test_load_transactions_unsupported():
    with pytest.raises(ValueError):
        load_transactions("statement.txt")


def test_write_summary(tmp_path):
    transactions = [
        {"date": "2023-01-01", "description": "Coffee", "amount": "-1.00", "balance": "99.00"},
        {"date": "2023-01-02", "description": "Tea", "amount": "-2.00", "balance": "97.00"},
    ]
    output = tmp_path / "summary.csv"
    path = write_summary(transactions, str(output))
    assert path == output

    with output.open() as f:
        rows = list(csv.reader(f))

    assert rows[0] == [
        "date",
        "description",
        "amount",
        "balance",
        "category",
        "action",
        "url",
        "email",
        "phone",
    ]
    assert rows[1] == ["2023-01-01", "Coffee", "-1.00", "99.00", "", "", "", "", ""]
    assert rows[2] == ["2023-01-02", "Tea", "-2.00", "97.00", "", "", "", "", ""]
    assert rows[3] == []
    assert rows[4] == [GLOBAL_DISCLAIMER]


def test_write_pdf_summary(tmp_path):
    transactions = [
        {"date": "2023-01-01", "description": "Coffee", "amount": "-1.00", "balance": "99.00"},
    ]
    output = tmp_path / "summary.pdf"
    path = write_pdf_summary(transactions, str(output), [])
    assert path == output

    with pdfplumber.open(output) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)

    assert "Coffee" in text
    assert GLOBAL_DISCLAIMER.replace("\n", " ") in text.replace("\n", " ")


def test_write_pdf_summary_long_description(tmp_path):
    long_desc = "Very long description " * 10
    transactions = [
        {"date": "2023-01-01", "description": long_desc, "amount": "-1.00", "balance": "99.00"},
    ]
    output = tmp_path / "long.pdf"
    write_pdf_summary(transactions, str(output), [])

    with pdfplumber.open(output) as pdf:
        table = pdf.pages[0].extract_table()
        assert table
        assert all(len(row) == 9 for row in table if row)
        text = " ".join(page.extract_text() or "" for page in pdf.pages)

    assert "Very long description" in text


def test_format_terminal_summary():
    transactions = [
        {"date": "2023-01-01", "description": "Coffee", "amount": "-1.00", "balance": "99.00"},
    ]
    text = format_terminal_summary(transactions, [])
    assert "Coffee" in text
    assert "category" in text.splitlines()[0]
    assert GLOBAL_DISCLAIMER in text


def test_write_summary_pdf(tmp_path):
    transactions = [{"date": "2023-01-01", "description": "Coffee", "amount": "-1.00", "balance": "99.00"}]
    output = tmp_path / "out.pdf"
    path = write_summary(transactions, str(output))
    assert path == output

    with pdfplumber.open(output) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)

    assert "Coffee" in text
    assert GLOBAL_DISCLAIMER.replace("\n", " ") in text.replace("\n", " ")


def test_write_summary_terminal():
    transactions = [{"date": "2023-01-01", "description": "Coffee", "amount": "-1.00", "balance": "99.00"}]
    text = write_summary(transactions, "terminal")
    assert "Coffee" in text
    assert GLOBAL_DISCLAIMER in text


def test_cancellation_filtering(tmp_path):
    recs = [
        Recommendation(
            transaction=Transaction(date="2024-01-01", description="Spotify", amount="-9.99"),
            category="spotify",
            action="Cancel",
            info={"url": "cancel-url"},
        )
    ]
    output = tmp_path / "cancel.pdf"
    write_pdf_summary(recs, str(output))
    with pdfplumber.open(output) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages).lower()
    assert "spotify" in text
    assert "netflix" not in text

    term = format_terminal_summary(recs)
    assert "- spotify:" in term.lower()
    assert "netflix" not in term.lower()
