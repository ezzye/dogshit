from bankcleanr.llm.mistral import MistralAdapter
from bankcleanr.transaction import Transaction


class DummyClient:
    def chat(self, *args, **kwargs):
        class Choice:
            message = type("M", (), {"content": '{"category": "coffee", "new_rule": ".*COFFEE.*"}'})()

        class Resp:
            choices = [Choice()]

        return Resp()


def test_classify_parses_json():
    adapter = MistralAdapter(api_key="dummy")
    adapter.client = DummyClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"


def test_retries_then_unknown():
    calls = {"n": 0}

    class FailingClient:
        def chat(self, *args, **kwargs):
            calls["n"] += 1
            raise RuntimeError("boom")

    adapter = MistralAdapter(api_key="dummy")
    adapter.client = FailingClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]
    assert calls["n"] == 3

