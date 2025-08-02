import json
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import jsonschema
from bankcleanr.extractor import extract_transactions

SCHEMA = json.load(open('schemas/transaction_v1.json'))


def _create_pdf(path: str) -> None:
    lines = [
        "Barclays Bank PLC",
        "Date Description Amount Balance",
        "01 Jan 2024 Coffee Shop -3.50 996.50",
        "02 Jan 2024 Salary 2000.00 2996.50",
    ]
    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
    c.save()


def test_extract_transactions():
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = os.path.join(tmp, 'barclays.pdf')
        _create_pdf(pdf_path)
        records = extract_transactions(pdf_path)
        assert len(records) == 2
        assert records[0]['description'] == 'Coffee Shop'
        for rec in records:
            jsonschema.validate(rec, SCHEMA)
