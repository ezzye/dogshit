from behave import given, when, then
import subprocess
from pathlib import Path
import re
from behave import use_step_matcher
import os
from bankcleanr.reports.disclaimers import GLOBAL_DISCLAIMER
from bankcleanr.cli import DEFAULT_OUTDIR

use_step_matcher("re")

@when('I run the bankcleanr config command')
def run_config(context):
    context.result = subprocess.run(['python', '-m', 'bankcleanr', 'config'], capture_output=True)

@then('the exit code is 0')
def check_exit(context):
    assert context.result.returncode == 0


@when(r'I run the bankcleanr parse command with "(?P<pdf>[^"]+)"')
def run_parse(context, pdf):
    root = Path(__file__).resolve().parents[2]
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "parse", str(root / pdf)],
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^\"]+)"(?: to "(?P<outfile>[^\"]+)")?')
def run_analyse(context, pdf, outfile=None):
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / DEFAULT_OUTDIR / (outfile or "summary.csv")
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf)]
        + (["--output", outfile] if outfile else []),
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^"]+)" with pdf "(?P<pdfout>[^"]+)"')
def run_analyse_pdf_option(context, pdf, pdfout):
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / DEFAULT_OUTDIR / pdfout
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf), "--pdf", pdfout],
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command on directory "(?P<dir>[^"]+)" with pdf "(?P<pdfout>[^"]+)"')
def run_analyse_directory_pdf_option(context, dir, pdfout):
    """Analyse a directory of statements writing the results to a PDF."""
    run_analyse_pdf_option(context, dir, pdfout)


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^"]+)" in outdir "(?P<dir>[^"]+)"')
def run_analyse_outdir(context, pdf, dir):
    root = Path(__file__).resolve().parents[2]
    out = root / dir
    context.summary_path = out / "summary.csv"
    if context.summary_path.exists():
        context.summary_path.unlink()
    out.mkdir(exist_ok=True)
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf), "--outdir", dir],
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^"]+)" with terminal output')
def run_analyse_terminal_option(context, pdf):
    root = Path(__file__).resolve().parents[2]
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf), "--terminal"],
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^"]+)" with verbose output')
def run_analyse_verbose_option(context, pdf):
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / DEFAULT_OUTDIR / "summary.csv"
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf), "--verbose"],
        capture_output=True,
        cwd=root,
    )


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^"]+)" to "(?P<outfile>[^"]+)" with terminal output')
def run_analyse_output_terminal(context, pdf, outfile):
    """Run analyse writing to a file and showing terminal output."""
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / DEFAULT_OUTDIR / outfile
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr",
            "analyse",
            str(root / pdf),
            "--output",
            outfile,
            "--terminal",
        ],
        capture_output=True,
        cwd=root,
    )


@then('the summary file exists')
def summary_exists(context):
    assert context.summary_path.exists()


@then('the summary contains the disclaimer')
def summary_contains_disclaimer(context):
    text = context.summary_path.read_text()
    assert GLOBAL_DISCLAIMER in text


@then('the PDF summary contains the disclaimer')
def pdf_summary_contains_disclaimer(context):
    import pdfplumber
    with pdfplumber.open(context.summary_path) as pdf:
        content = "".join(page.extract_text() or "" for page in pdf.pages)
    assert GLOBAL_DISCLAIMER.replace("\n", " ") in content.replace("\n", " ")


@then('the terminal output contains the disclaimer')
def terminal_output_contains_disclaimer(context):
    output = context.result.stdout.decode()
    assert GLOBAL_DISCLAIMER in output


@then('the terminal output contains the disclaimer once')
def terminal_output_contains_disclaimer_once(context):
    """Ensure the disclaimer appears exactly once in terminal output."""
    output = context.result.stdout.decode()
    assert output.count(GLOBAL_DISCLAIMER) == 1


@then(r'the terminal output contains "(?P<text>[^"]+)"')
def terminal_output_contains_text(context, text):
    output = context.result.stdout.decode()
    assert text in output


@then('the terminal output shows savings')
def terminal_output_shows_savings(context):
    output = context.result.stdout.decode().lower()
    assert "potential savings" in output


@given("an API key is configured")
def api_key_configured(context):
    context._orig_key = os.getenv("OPENAI_API_KEY")
    if context._orig_key is None or context._orig_key.lower() == "dummy":
        os.environ["OPENAI_API_KEY"] = "dummy"


@then(r'the summary actions include "(?P<label>[^"]+)"')
def summary_actions_include(context, label):
    import csv
    with open(context.summary_path) as f:
        reader = csv.DictReader(f)
        acts = [row["action"] for row in reader]
    assert label in acts
