import os
import subprocess
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from behave import given, when, then


def _create_pdf(path: str) -> None:
    lines = [
        "Barclays Bank PLC",
        "Date Description Amount Balance",
        "01 Jan 2024 Coffee Shop -3.50 996.50",
        "02 Jan 2024 Salary 2000.00 2996.50",
    ]
    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
    c.save()


@given("a sample Barclays statement")
def step_given_sample(context):
    context.tmpdir = tempfile.TemporaryDirectory()
    context.pdf_path = os.path.join(context.tmpdir.name, "barclays.pdf")
    _create_pdf(context.pdf_path)


@when("I run the extractor")
def step_run_extractor(context):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        ["python", "-m", "bankcleanr.cli", "extract", context.pdf_path, context.jsonl_path],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
    )


@then("a JSONL file with 2 transactions is created")
def step_then_check(context):
    with open(context.jsonl_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    assert len(lines) == 2
    context.tmpdir.cleanup()
