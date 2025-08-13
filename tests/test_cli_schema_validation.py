from jsonschema import ValidationError
from typer.testing import CliRunner

from bankcleanr import cli


def test_cli_validates_records(tmp_path, monkeypatch):
    runner = CliRunner()

    def fake_extract(pdf_path: str, bank: str = "barclays"):
        return [{"date": "01 Jan 2024", "description": "x", "type": "credit"}]  # missing amount

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(cli.app, ["extract", str(pdf), str(out)])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)


def test_cli_handles_missing_amount(tmp_path, monkeypatch):
    runner = CliRunner()

    def fake_extract(pdf_path: str, bank: str = "barclays"):
        return [
            {
                "date": "01 Jan 2024",
                "description": "x",
                "amount": None,
                "merchant_signature": "",
            }
        ]

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(cli.app, ["extract", str(pdf), str(out)])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)


def test_cli_parse_alias(tmp_path, monkeypatch):
    runner = CliRunner()

    def fake_extract(pdf_path: str, bank: str = "barclays"):
        return [
            {
                "date": "01 Jan 2024",
                "description": "x",
                "amount": "1",
                "merchant_signature": "",
                "type": "credit",
            }
        ]

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(cli.app, ["parse", str(pdf), str(out)])
    assert result.exit_code == 0
    assert (
        out.read_text()
        == '{"date": "01 Jan 2024", "description": "x", "amount": "1", "merchant_signature": "", "type": "credit"}\n'
    )
