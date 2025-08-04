import json
import os
import tempfile

import pytest
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
    elif bank == "hsbc":
        lines = [
            "HSBC Bank",
            "Date Description Amount Balance",
            "01 Jan 2024 Groceries -10.00 990.00",
            "02 Jan 2024 Salary 2000.00 2990.00",
        ]
    elif bank == "lloyds":
        lines = [
            "Lloyds Bank",
            "Date Description Amount Balance",
            "01 Jan 2024 Rent -500.00 500.00",
            "02 Jan 2024 Salary 2000.00 2500.00",
        ]
    else:
        lines = ["Placeholder Bank"]

    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
    c.save()


@pytest.mark.parametrize(
    "bank,expected",
    [
        ("barclays", 2),
        ("hsbc", 2),
        ("lloyds", 2),
        ("placeholder", 1),
    ],
)
def test_extract_transactions(bank, expected):
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, f"{bank}.pdf")
        _create_pdf(pdf_path, bank)
        records = extract_transactions(pdf_path, bank=bank)
        assert len(records) == expected
        for rec in records:
            jsonschema.validate(rec, SCHEMA)
