import json
from pathlib import Path

import jsonschema
import pytest

from bankcleanr.extractor import extract_transactions

SCHEMA = json.load(open("schemas/transaction_v1.json"))
FIXTURE_DIR = Path("tests/fixtures/coop")

STATEMENTS = [
    (FIXTURE_DIR / "statement_1.pdf", FIXTURE_DIR / "statement_1.json"),
    (FIXTURE_DIR / "statement_2.pdf", FIXTURE_DIR / "statement_2.json"),
    (FIXTURE_DIR / "statement_3.pdf", FIXTURE_DIR / "statement_3.json"),
]


@pytest.mark.parametrize("pdf_path,json_path", STATEMENTS)
def test_extract_transactions(pdf_path: Path, json_path: Path) -> None:
    expected = json.load(open(json_path))
    records = list(extract_transactions(str(pdf_path), bank="coop"))
    assert records == expected
    for rec in records:
        jsonschema.validate(rec, SCHEMA)
        assert rec["date"]
        assert rec["description"]
        assert rec["amount"].startswith(("+", "-"))


def test_extract_transactions_directory() -> None:
    records = list(extract_transactions(str(FIXTURE_DIR), bank="coop"))
    expected_count = sum(len(json.load(open(jp))) for _, jp in STATEMENTS)
    assert len(records) == expected_count
