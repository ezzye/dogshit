from pathlib import Path
from typer.testing import CliRunner

from bankcleanr.cli import app, SAMPLE_STATEMENT
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
