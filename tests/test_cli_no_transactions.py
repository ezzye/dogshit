from typer.testing import CliRunner

from bankcleanr import cli


def test_cli_exits_when_no_transactions(tmp_path, monkeypatch):
    runner = CliRunner()

    def fake_extract(pdf_path: str, bank: str | None = None):
        return []

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(cli.app, ["extract", str(pdf), str(out)])
    assert result.exit_code != 0
    output = result.stdout + result.stderr
    assert "No transactions extracted" in output


def test_cli_allows_missing_bank(tmp_path, monkeypatch):
    runner = CliRunner()
    called: dict[str, str | None] = {}

    def fake_extract(pdf_path: str, bank: str | None = None):
        called["bank"] = bank
        return []

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    runner.invoke(cli.app, ["extract", str(pdf), str(out)])
    assert called["bank"] is None
