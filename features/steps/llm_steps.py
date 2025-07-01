from behave import given, when, then

from bankcleanr.transaction import Transaction
from bankcleanr.llm import classify_transactions, PROVIDERS
from bankcleanr.llm.openai import OpenAIAdapter


@given("transactions requiring LLM")
def transactions_for_llm(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]


@given('the OpenAI adapter is mocked to return "{label}"')
def mock_adapter(context, label):
    class DummyAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            pass

        def classify_transactions(self, transactions):
            return [label for _ in transactions]

    context.original = PROVIDERS["openai"]
    PROVIDERS["openai"] = DummyAdapter


@when("I classify transactions with the LLM")
def classify_with_llm(context):
    context.labels = classify_transactions(context.txs, provider="openai")


@then("the LLM labels are")
def check_labels(context):
    expected = [row[0] for row in context.table.rows]
    assert context.labels == expected
    if hasattr(context, "original"):
        PROVIDERS["openai"] = context.original
