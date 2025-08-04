import os
import pytest

from backend.llm_adapter import AbstractAdapter, DailyCostTracker, cost_tracker


class DummyAdapter(AbstractAdapter):
    def __init__(self, responses, fail_times=0):
        super().__init__("test-model", batch_size=2, max_retries=3)
        self.responses = responses
        self.fail_times = fail_times
        self.calls = 0

    def _send(self, prompts):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("boom")
        labels = []
        tokens = 0
        for p in prompts:
            data = self.responses[p]
            labels.append((data["label"], data["confidence"]))
            tokens += data["tokens"]
        return {"labels": labels, "usage": {"total_tokens": tokens}}


def test_retries(monkeypatch):
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 10}}, fail_times=1)
    out = adapter.classify(["a"], job_id=1)
    assert out[0]["label"] == "x"
    assert adapter.calls == 2


def test_cost_limit(monkeypatch):
    tracker = DailyCostTracker(limit=0.0001)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 1000}})
    with pytest.raises(RuntimeError):
        adapter.classify(["a"], job_id=1)
