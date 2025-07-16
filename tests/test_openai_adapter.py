import asyncio
from bankcleanr.llm.openai import OpenAIAdapter
from bankcleanr.transaction import Transaction

class DummyChat:
    async def ainvoke(self, messages):
        class R:
            content = '{"category": "coffee", "reasons_to_cancel": ["expensive"], "checklist": ["call bank"]}'
        return R()


def test_aclassify_parses_json(monkeypatch):
    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: DummyChat())
    adapter = OpenAIAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    result = asyncio.run(adapter._aclassify(tx))
    assert result["category"] == "coffee"
    assert result["reasons_to_cancel"] == ["expensive"]
    assert result["checklist"] == ["call bank"]


class SlowChat:
    def __init__(self):
        self.running = 0
        self.max_running = 0

    async def ainvoke(self, messages):
        self.running += 1
        self.max_running = max(self.max_running, self.running)
        await asyncio.sleep(0.01)
        self.running -= 1
        class R:
            content = '{"category": "coffee"}'
        return R()


def test_aclassify_throttles_concurrency(monkeypatch):
    chat = SlowChat()
    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: chat)
    adapter = OpenAIAdapter(api_key="dummy", max_concurrency=5)
    txs = [
        Transaction(date="2024-01-01", description=f"tx{i}", amount="-1")
        for i in range(20)
    ]
    adapter.classify_transactions(txs)
    assert chat.max_running <= 5


class FailingChat:
    async def ainvoke(self, messages):
        raise RuntimeError("network down")


def test_classify_returns_unknown_on_failure(monkeypatch):
    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: FailingChat())
    adapter = OpenAIAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    labels = adapter.classify_transactions([tx])
    assert labels == ["unknown"]


def test_classify_transactions_parses_json(monkeypatch):
    """Ensure classify_transactions stores parsed JSON."""
    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: DummyChat())
    adapter = OpenAIAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    labels = adapter.classify_transactions([tx])
    assert labels == ["coffee"]
    assert adapter.last_details[0] == {
        "category": "coffee",
        "reasons_to_cancel": ["expensive"],
        "checklist": ["call bank"],
    }


class FencedChat:
    async def ainvoke(self, messages):
        class R:
            content = "```json\n{\"category\": \"coffee\"}\n```"

        return R()


def test_aclassify_handles_json_fences(monkeypatch):
    monkeypatch.setattr(
        "bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: FencedChat()
    )
    adapter = OpenAIAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    result = asyncio.run(adapter._aclassify(tx))
    assert result == {"category": "coffee"}
