from behave import given, when, then

from bankcleanr.transaction import Transaction
from bankcleanr.llm import classify_transactions, PROVIDERS
from bankcleanr.llm.openai import OpenAIAdapter
import bankcleanr.llm.openai as openai_mod
import asyncio


@given("transactions requiring LLM")
def transactions_for_llm(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]


@given("{count:d} transactions requiring LLM")
def many_transactions_for_llm(context, count):
    context.txs = [
        Transaction(date="2024-01-01", description=f"tx {i}", amount="-1.00")
        for i in range(count)
    ]


def _mock_adapter(context, provider, label):
    provider = provider.lower()
    class DummyAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            pass

        def classify_transactions(self, transactions):
            return [label for _ in transactions]

    context.original = PROVIDERS[provider]
    context.provider = provider
    PROVIDERS[provider] = DummyAdapter


@given('the OpenAI adapter is mocked to return "{label}"')
def mock_openai_adapter(context, label):
    _mock_adapter(context, "openai", label)


@given('the {provider} adapter is mocked to return "{label}"')
def mock_named_adapter(context, provider, label):
    _mock_adapter(context, provider, label)


@when("I classify transactions with the LLM")
def classify_with_llm(context):
    provider = getattr(context, "provider", "openai")
    context.labels = classify_transactions(context.txs, provider=provider)


@then("the LLM labels are")
def check_labels(context):
    expected = [row[0] for row in context.table.rows]
    assert context.labels == expected
    if hasattr(context, "original"):
        provider = getattr(context, "provider", "openai")
        PROVIDERS[provider] = context.original


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


@given("the OpenAI API is replaced with a counting stub")
def counting_stub(context):
    class CountingChat:
        def __init__(self):
            self.running = 0
            self.max_running = 0

        async def apredict_messages(self, messages):
            self.running += 1
            self.max_running = max(self.max_running, self.running)
            await asyncio.sleep(0.01)
            self.running -= 1
            class R:
                content = "coffee"
            return R()

    context.chat = CountingChat()
    context.original_chat = openai_mod.ChatOpenAI
    openai_mod.ChatOpenAI = lambda *a, **k: context.chat


@when("I classify transactions with the throttled adapter")
def classify_with_throttled(context):
    adapter = OpenAIAdapter(api_key="dummy", max_concurrency=5)
    adapter.classify_transactions(context.txs)
    context.max_running = context.chat.max_running
    openai_mod.ChatOpenAI = context.original_chat


@then("no more than 5 concurrent requests were sent")
def check_throttling(context):
    assert context.max_running <= 5
