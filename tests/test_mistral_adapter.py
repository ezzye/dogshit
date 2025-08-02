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

