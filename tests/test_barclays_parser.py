import json
import os
import tempfile

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import jsonschema

from bankcleanr.extractor import extract_transactions

SCHEMA = json.load(open("schemas/transaction_v1.json"))


def _create_pdf(path: str, bank: str) -> None:
    if bank == "barclays":
        lines = [
            "Barclays Bank PLC",
            "Date Description Amount Balance",
            "01 Jan 2024 Coffee Shop -3.50 996.50",
            "02 Jan 2024 Salary 2000.00 2996.50",
        ]
    else:
        lines = ["Placeholder Bank"]

    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
    c.save()


def test_extract_transactions_barclays():
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, "barclays.pdf")
        _create_pdf(pdf_path, "barclays")
        records = extract_transactions(pdf_path, bank="barclays")
        assert len(records) == 2
        assert records[0]["description"] == "Coffee Shop"
        for rec in records:
            jsonschema.validate(rec, SCHEMA)


def test_extract_transactions_placeholder():
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, "placeholder.pdf")
        _create_pdf(pdf_path, "placeholder")
        records = extract_transactions(pdf_path, bank="placeholder")
        assert len(records) == 1
        assert records[0]["description"] == "placeholder"
        for rec in records:
            jsonschema.validate(rec, SCHEMA)
