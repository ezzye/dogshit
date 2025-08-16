from typer.testing import CliRunner

from bankcleanr import cli


def test_cli_exits_when_no_transactions(tmp_path, monkeypatch):
    runner = CliRunner()

    def fake_extract(pdf_path: str, bank: str = "barclays"):
        return []

    monkeypatch.setattr(cli, "extract_transactions", fake_extract)

    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(
        cli.app, ["extract", str(pdf), str(out), "--bank", "barclays"]
    )
    assert result.exit_code != 0
    output = result.stdout + result.stderr
    assert "No transactions extracted" in output


def test_cli_requires_bank(tmp_path):
    runner = CliRunner()
    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    out = tmp_path / "out.jsonl"
    result = runner.invoke(cli.app, ["extract", str(pdf), str(out)])
    assert result.exit_code != 0
    output = result.stdout + result.stderr
    assert "Missing option '--bank'" in output
