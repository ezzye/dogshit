from behave import given, when, then
from pathlib import Path
import tempfile
import yaml
import importlib
from bankcleanr.transaction import Transaction
from bankcleanr.rules import regex
from bankcleanr.rules import heuristics


@given("sample transactions")
def given_transactions(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Amazon Prime membership", amount="-8.99"),
        Transaction(date="2024-01-03", description="Dropbox yearly", amount="-119.00"),
        Transaction(date="2024-01-04", description="Coffee", amount="-2.00"),
    ]


@when("I classify transactions locally")
def classify(context):
    context.labels = heuristics.classify_transactions(context.txs)


@then("the labels are")
def check_labels(context):
    expected = [row[0] for row in context.table.rows]
    assert context.labels == expected


@given("a heuristics file containing")
def heuristics_file(context):
    data = {row["label"]: row["pattern"] for row in context.table}
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(yaml.safe_dump(data).encode())
    tmp.close()
    context.heuristics_path = Path(tmp.name)
    context.orig_heuristics = regex.HEURISTICS_PATH
    regex.HEURISTICS_PATH = Path(tmp.name)
    regex.reload_patterns(Path(tmp.name))
    importlib.reload(heuristics)


@given('a transaction "{description}"')
def single_transaction(context, description):
    context.txs = [Transaction(date="2024-01-01", description=description, amount="-1.00")]


