from datetime import date, timedelta

import pytest
from bankcleanr.llm.cost_manager import DailyCostManager


def test_blocks_when_limit_exceeded(tmp_path):
    path = tmp_path / "cost.json"
    manager = DailyCostManager(max_cost=1.0, path=path, today_fn=lambda: date(2024, 1, 1))
    manager.check_and_add(0.6)
    with pytest.raises(RuntimeError):
        manager.check_and_add(0.5)


def test_resets_each_day(tmp_path):
    today = date(2024, 1, 1)
    path = tmp_path / "cost.json"
    manager = DailyCostManager(max_cost=2.0, path=path, today_fn=lambda: today)
    manager.check_and_add(1.5)
    # simulate next day
    manager.today_fn = lambda: today + timedelta(days=1)
    manager.check_and_add(1.5)  # should not raise
    assert manager.spend == 1.5


def test_adapter_blocks_on_limit(monkeypatch, tmp_path):
    from bankcleanr.llm.openai import OpenAIAdapter

    class DummyChat:
        def __init__(self):
            self.called = False

        async def ainvoke(self, msgs):
            self.called = True
            class R:
                content = "{\"category\": \"coffee\"}"
            return R()

    chat = DummyChat()
    monkeypatch.setattr("bankcleanr.llm.openai.ChatOpenAI", lambda *a, **k: chat)
    manager = DailyCostManager(max_cost=0.0, path=tmp_path / "cost.json", today_fn=lambda: date(2024, 1, 1))
    monkeypatch.setattr("bankcleanr.llm.openai.cost_manager", manager)
    adapter = OpenAIAdapter(api_key="key")
    details = adapter.classify_transactions([{"description": "coffee"}])
    assert chat.called is False
    assert details[0]["category"] == "unknown"
