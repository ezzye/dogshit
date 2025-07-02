import asyncio
from bankcleanr.llm.openai import OpenAIAdapter
from bankcleanr.transaction import Transaction

class DummyChat:
    async def apredict_messages(self, messages):
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
