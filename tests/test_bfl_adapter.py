from bankcleanr.llm.bfl import BFLAdapter
from bankcleanr.transaction import Transaction


class DummyChat:
    async def ainvoke(self, messages):
        class R:
            content = '{"category": "coffee", "new_rule": ".*COFFEE.*"}'

        return R()


def test_classify_parses_json(monkeypatch):
    monkeypatch.setattr(
        "bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: DummyChat()
    )
    adapter = BFLAdapter(api_key="dummy")
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"


def test_retries_then_unknown(monkeypatch):
    class DummyChat:
        async def ainvoke(self, messages):
            return type("R", (), {"content": ""})()

    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: DummyChat())

    calls = {"n": 0}

    def failing_classify(transactions):
        calls["n"] += 1
        raise RuntimeError("boom")

    adapter = BFLAdapter(api_key="dummy")
    adapter.delegate.classify_transactions = failing_classify
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]
    assert calls["n"] == 3

