from behave import when, then
import subprocess
from pathlib import Path
from bankcleanr.reports.disclaimers import GLOBAL_DISCLAIMER

@when('I run the bankcleanr config command')
def run_config(context):
    context.result = subprocess.run(['python', '-m', 'bankcleanr', 'config'], capture_output=True)

@then('the exit code is 0')
def check_exit(context):
    assert context.result.returncode == 0


@when('I run the bankcleanr analyse command with "{pdf}"')
def run_analyse(context, pdf):
    root = Path(__file__).resolve().parents[2]
    context.summary_path = root / "summary.csv"
    if context.summary_path.exists():
        context.summary_path.unlink()
    context.result = subprocess.run(
        ["python", "-m", "bankcleanr", "analyse", str(root / pdf)],
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
