import json
import jsonschema
from pathlib import Path
from bankcleanr.io.jsonl import write_jsonl
from bankcleanr.transaction import Transaction

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "transaction_v1.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())


def test_write_jsonl(tmp_path):
    txs = [
        Transaction(date="2024-01-01", description="Pay 12-34-56 12345678", amount="-1.00", balance="99.00"),
        {"date": "2024-01-02", "description": "Coffee 12345678", "amount": "-2.00", "balance": "97.00"},
    ]
    output = tmp_path / "out.jsonl"
    path = write_jsonl(txs, str(output))
    assert path == output

    lines = output.read_text().splitlines()
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        jsonschema.validate(record, SCHEMA)
        assert "****" in record["description"]
