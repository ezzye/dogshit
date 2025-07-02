from behave import when, then
import subprocess
from pathlib import Path
import re
from behave import use_step_matcher
from bankcleanr.reports.disclaimers import GLOBAL_DISCLAIMER

use_step_matcher("re")

@when('I run the bankcleanr config command')
def run_config(context):
    context.result = subprocess.run(['python', '-m', 'bankcleanr', 'config'], capture_output=True)

@then('the exit code is 0')
def check_exit(context):
    assert context.result.returncode == 0


@when(r'I run the bankcleanr analyse command with "(?P<pdf>[^\"]+)"(?: to "(?P<outfile>[^\"]+)")?')
def run_analyse(context, pdf, outfile=None):
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / (outfile or "summary.csv")
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
    context.summary_path = root / pdfout
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf), "--pdf", pdfout],
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
