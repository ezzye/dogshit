import pytest
from bankcleanr.llm.anthropic import AnthropicAdapter
from bankcleanr.transaction import Transaction


class DummyClient:
    def __init__(self):
        class Messages:
            def create(self, *args, **kwargs):
                class Msg:
                    text = '{"category": "coffee", "new_rule": ".*COFFEE.*"}'

                class Resp:
                    content = [Msg()]

                return Resp()

        self.messages = Messages()


def test_classify_parses_json(monkeypatch):
    adapter = AnthropicAdapter(api_key="dummy")
    adapter.client = DummyClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"

