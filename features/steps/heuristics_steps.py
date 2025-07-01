from behave import given, when, then
from bankcleanr.transaction import Transaction
from bankcleanr.rules.heuristics import classify_transactions


@given("sample transactions")
def given_transactions(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee", amount="-2.00"),
    ]


@when("I classify transactions locally")
def classify(context):
    context.labels = classify_transactions(context.txs)


@then("the labels are")
def check_labels(context):
    expected = [row[0] for row in context.table.rows]
    assert context.labels == expected
