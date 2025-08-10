import os
import subprocess
import tempfile

from behave import given, when, then  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _create_pdf(path: str, bank: str) -> None:
    if bank == "barclays":
        lines = [
            "Barclays Bank PLC",
            "Date Description Amount Balance",
            "01 Jan 2024 Coffee Shop -3.50 996.50",
            "02 Jan 2024 Salary 2000.00 2996.50",
        ]
    elif bank == "hsbc":
        lines = [
            "HSBC Bank",
            "Date Description Amount Balance",
            "01 Jan 2024 Groceries -10.00 990.00",
            "02 Jan 2024 Salary 2000.00 2990.00",
        ]
    elif bank == "lloyds":
        lines = [
            "Lloyds Bank",
            "Date Description Amount Balance",
            "01 Jan 2024 Rent -500.00 500.00",
            "02 Jan 2024 Salary 2000.00 2500.00",
        ]
    elif bank == "coop":
        lines = [
            "Co-op Bank",
            "Date Description Moneyout Moneyin Balance",
            "01 Jan 2024 Coffee Shop 3.50 0.00 996.50",
            "02 Jan 2024 Salary 0.00 2000.00 2996.50",
        ]
    else:
        lines = ["Placeholder Bank"]

    c = canvas.Canvas(path, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
    c.save()


@given("a sample {bank} statement")
def step_given_sample(context, bank):
    context.tmpdir = tempfile.TemporaryDirectory()
    context.pdf_path = os.path.join(context.tmpdir.name, f"{bank}.pdf")
    _create_pdf(context.pdf_path, bank)


@when("I run the {bank} extractor")
def step_run_extractor(context, bank):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr.cli",
            "extract",
            "--bank",
            bank,
            context.pdf_path,
            context.jsonl_path,
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )


@then("a JSONL file with {count:d} transactions is created")
def step_then_check(context, count):
    with open(context.jsonl_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    assert len(lines) == count
    context.tmpdir.cleanup()


@given("multiple {bank} statements")
def step_given_multiple(context, bank):
    context.tmpdir = tempfile.TemporaryDirectory()
    context.pdf_dir = context.tmpdir.name
    for name in ["a.pdf", "b.pdf"]:
        _create_pdf(os.path.join(context.pdf_dir, name), bank)


@when("I run the {bank} extractor on the directory")
def step_run_extractor_dir(context, bank):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr.cli",
            "extract",
            "--bank",
            bank,
            context.pdf_dir,
            context.jsonl_path,
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )
