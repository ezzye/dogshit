import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bankcleanr import cli

FIXTURES = [
    ("hsbc", Path("tests/fixtures/hsbc/statement_1.pdf")),
    ("lloyds", Path("tests/fixtures/lloyds/statement_1.pdf")),
    ("coop", Path("tests/fixtures/coop/statement_1.pdf")),
    ("barclays", Path("tests/fixtures/barclays/statement_1.pdf")),
]


@pytest.mark.parametrize("bank,pdf_path", FIXTURES)
def test_cli_parses_each_bank(bank: str, pdf_path: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "out.jsonl"
    result = runner.invoke(
        cli.app, ["extract", str(pdf_path), str(out), "--bank", bank]
    )
    assert result.exit_code == 0
    lines = out.read_text().strip().splitlines()
    assert lines
    for line in lines:
        record = json.loads(line)
        assert record["date"]
        assert record["amount"].startswith(("+", "-"))
        assert record["type"] in {"credit", "debit"}
