import pytest

from bankcleanr.extractor import extract_transactions
from bankcleanr.parsers import PARSER_REGISTRY


def test_extract_transactions_unknown_bank():
    available = ", ".join(sorted(PARSER_REGISTRY))
    with pytest.raises(ValueError) as excinfo:
        list(extract_transactions("dummy.pdf", bank="unknown"))
    assert str(excinfo.value) == (
        f"Unsupported bank 'unknown'. Available banks: {available}"
    )


def test_extract_transactions_empty_directory(tmp_path):
    with pytest.raises(ValueError) as excinfo:
        list(extract_transactions(tmp_path))
    assert str(excinfo.value) == f"No PDFs found in directory: {tmp_path}"


def test_extract_transactions_adds_type(monkeypatch, tmp_path):
    class DummyParser:
        def parse(self, pdf_path):  # pragma: no cover - simple helper
            return [
                {
                    "date": "2024-01-01",
                    "description": "x",
                    "amount": "+1.00",
                    "merchant_signature": "sig",
                }
            ]

    monkeypatch.setitem(PARSER_REGISTRY, "dummy", DummyParser)
    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    records = list(extract_transactions(str(pdf), bank="dummy"))
    assert records == [
        {
            "date": "2024-01-01",
            "description": "x",
            "amount": "+1.00",
            "merchant_signature": "sig",
            "type": "credit",
        }
    ]
    PARSER_REGISTRY.pop("dummy", None)
