from pathlib import Path
import json
import jsonschema
from typer.testing import CliRunner

from bankcleanr.cli import app, SAMPLE_STATEMENT, DEFAULT_OUTDIR
from bankcleanr.reports.disclaimers import GLOBAL_DISCLAIMER


def test_analyse_outdir_creates_files(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "analyse",
            str(SAMPLE_STATEMENT),
            "--outdir",
            str(tmp_path),
            "--pdf",
            "report.pdf",
        ],
    )
    assert result.exit_code == 0
    csv = tmp_path / "summary.csv"
    pdf = tmp_path / "report.pdf"
    assert csv.exists()
    assert pdf.exists()
    assert GLOBAL_DISCLAIMER in csv.read_text()


def test_analyse_verbose_outputs_paths(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "analyse",
            str(SAMPLE_STATEMENT),
            "--outdir",
            str(tmp_path),
            "--verbose",
        ],
    )
    assert result.exit_code == 0
    csv = tmp_path / "summary.csv"
    assert csv.exists()
    assert str(SAMPLE_STATEMENT) in result.stdout


def test_analyse_default_outdir(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            [
                "analyse",
                str(SAMPLE_STATEMENT),
                "--pdf",
                "report.pdf",
            ],
        )
        assert result.exit_code == 0
        csv = Path(DEFAULT_OUTDIR) / "summary.csv"
        pdf = Path(DEFAULT_OUTDIR) / "report.pdf"
        assert csv.exists()
        assert pdf.exists()
        assert GLOBAL_DISCLAIMER in csv.read_text()


def test_parse_jsonl_option(tmp_path):
    runner = CliRunner()
    out = tmp_path / "tx.jsonl"
    result = runner.invoke(
        app,
        ["parse", str(SAMPLE_STATEMENT), "--jsonl", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    lines = out.read_text().splitlines()
    assert lines
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "transaction_v1.json").read_text())
    for line in lines:
        data = json.loads(line)
        jsonschema.validate(data, schema)
