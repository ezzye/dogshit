import os
from tempfile import NamedTemporaryFile

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bankcleanr.io.pdf import generic
from bankcleanr.transaction import Transaction
from bankcleanr.io.pdf import barclays
from pathlib import Path


def _make_simple_pdf(rows):
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    c = canvas.Canvas(tmp.name, pagesize=letter)
    y = 750
    for row in rows:
        x = 50
        for cell in row:
            c.drawString(x, y, cell)
            x += 100
        y -= 20
    c.save()
    return tmp.name


def test_parse_pdf_regex():
    rows = [
        ["Date", "Description", "Amount", "Balance"],
        ["01 Jan", "Coffee", "-1.00", "99.00"],
        ["02 Jan", "Tea", "-2.00", "97.00"],
    ]
    path = _make_simple_pdf(rows)
    try:
        txs = generic.parse_pdf(path)
    finally:
        os.unlink(path)
    assert txs[0].description == "Coffee"
    assert txs[1].amount == "-2.00"


def test_parse_money_in_out_columns():
    rows = [
        ["Date", "Description", "Money out", "Money in", "Balance"],
        ["01 Jan", "Coffee", "1.00", "0.00", "99.00"],
        ["02 Jan", "Salary", "0.00", "100.00", "199.00"],
    ]
    path = _make_simple_pdf(rows)
    try:
        txs = generic.parse_pdf(path)
    finally:
        os.unlink(path)
    assert txs[0].amount == "-1.00"
    assert txs[1].amount == "100.00"


def test_parse_pdf_ocr_fallback(monkeypatch):
    called = {}

    def fake_open(path):
        raise RuntimeError("fail")

    def fake_ocr(path):
        called["ocr"] = True
        return [{"date": "01 Jan"}]

    monkeypatch.setattr(generic, "pdfplumber", type("X", (), {"open": fake_open}))
    import types
    import sys
    fake_mod = types.SimpleNamespace(parse_pdf=fake_ocr)
    monkeypatch.setitem(sys.modules, "bankcleanr.io.pdf.ocr_fallback", fake_mod)
    result = generic.parse_pdf("dummy.pdf")
    assert called.get("ocr")
    assert isinstance(result[0], Transaction)
    assert result[0].date == "01 Jan"


def test_barclays_sample_parse():
    sample = Path("Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf")
    txs = barclays.parse_pdf(str(sample))
    assert len(txs) >= 5
    assert any("paypal" in tx.description.lower() for tx in txs)
