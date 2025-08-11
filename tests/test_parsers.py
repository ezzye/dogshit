import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import jsonschema
import pytest
from reportlab.pdfgen import canvas

from bankcleanr.extractor import extract_transactions

SCHEMA = json.load(open("schemas/transaction_v1.json"))
FIXTURE_DIR = Path("tests/fixtures/coop")

STATEMENTS = [
    (FIXTURE_DIR / "statement_1.pdf", FIXTURE_DIR / "statement_1.json"),
    (FIXTURE_DIR / "statement_2.pdf", FIXTURE_DIR / "statement_2.json"),
    (FIXTURE_DIR / "statement_3.pdf", FIXTURE_DIR / "statement_3.json"),
]


def _ensure_pdf(pdf_path: Path, json_path: Path) -> None:
    if pdf_path.exists():
        return
    records = json.load(open(json_path))
    c = canvas.Canvas(str(pdf_path))
    text = c.beginText(40, 800)
    first_date = datetime.fromisoformat(records[0]["date"])
    text.textLine(f"Statement date {first_date.strftime('%d %B %Y')}")
    for rec in records:
        d = datetime.fromisoformat(rec["date"])
        line = f"{d.strftime('%d %b')} {rec['description']} {abs(Decimal(rec['amount'])):.2f}"
        if rec["balance"] is not None:
            line += f" {abs(Decimal(rec['balance'])):.2f}"
        text.textLine(line)
    c.drawText(text)
    c.save()


for pdf, jsn in STATEMENTS:
    _ensure_pdf(pdf, jsn)


@pytest.mark.parametrize("pdf_path,json_path", STATEMENTS)
def test_extract_transactions(pdf_path: Path, json_path: Path) -> None:
    expected = json.load(open(json_path))
    records = list(extract_transactions(str(pdf_path), bank="coop"))
    def _norm(desc: str) -> str:
        return " ".join(desc.split())
    norm_expected = [{**r, "description": _norm(r["description"]) } for r in expected]
    norm_records = [{**r, "description": _norm(r["description"]) } for r in records]
    assert norm_records == norm_expected
    for rec in records:
        jsonschema.validate(rec, SCHEMA)
        assert rec["date"]
        assert rec["description"]
        assert rec["amount"].startswith(("+", "-"))


def test_extract_transactions_directory() -> None:
    records = list(extract_transactions(str(FIXTURE_DIR), bank="coop"))
    expected_count = sum(len(json.load(open(jp))) for _, jp in STATEMENTS)
    assert len(records) == expected_count
