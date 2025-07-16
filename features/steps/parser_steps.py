from behave import given, when, then
from tempfile import NamedTemporaryFile
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bankcleanr.io.pdf import generic


def _create_pdf(rows):
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    c = canvas.Canvas(tmp.name, pagesize=letter)
    y = 750
    for row in rows:
        x = 50
        for cell in row:
            c.drawString(x, y, cell)
            x += 100
        y -= 20
    c.save()
    return tmp.name


@given("a minimal statement PDF")
def given_pdf(context):
    rows = [
        ["Date", "Description", "Amount", "Balance"],
        ["01 Jan", "Coffee", "-1.00", "99.00"],
        ["02 Jan", "Tea", "-2.00", "97.00"],
    ]
    context.pdf_path = _create_pdf(rows)


@when("I parse the file")
def parse_file(context):
    context.transactions = generic.parse_pdf(context.pdf_path)
    os.unlink(context.pdf_path)


@then("the parser returns two transactions")
def check_transactions(context):
    assert len(context.transactions) == 2
    assert context.transactions[0].description == "Coffee"


@given("a statement PDF with Money in and out columns")
def given_in_out_pdf(context):
    rows = [
        ["Date", "Description", "Money out", "Money in", "Balance"],
        ["01 Jan", "Coffee", "1.00", "0.00", "99.00"],
        ["02 Jan", "Salary", "0.00", "100.00", "199.00"],
    ]
    context.pdf_path = _create_pdf(rows)


@then("the amounts reflect income and expenses")
def check_amount_signs(context):
    assert context.transactions[0].amount == "-1.00"
    assert context.transactions[1].amount == "100.00"
