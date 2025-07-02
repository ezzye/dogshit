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


@given("a transaction containing account details")
def transaction_with_account(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Send 12-34-56 12345678", amount="-1.00")
    ]


@when("I classify the transaction with a capture adapter")
def classify_with_capture(context):
    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            pass

        def classify_transactions(self, transactions):
            context.captured_descriptions = [tx.description for tx in transactions]
            return ["ok"]

    context.original = PROVIDERS["openai"]
    PROVIDERS["openai"] = CaptureAdapter
    classify_transactions(context.txs, provider="openai")
    PROVIDERS["openai"] = context.original


@then("the adapter received the masked transaction")
def check_masked_tx(context):
    assert context.captured_descriptions[0] == "Send ****3456 ****5678"
