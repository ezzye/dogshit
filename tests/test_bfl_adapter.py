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

