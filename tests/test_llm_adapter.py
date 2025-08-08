import pytest
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from backend.llm_adapter import (
    AbstractAdapter,
    AnthropicAdapter,
    AzureAdapter,
    DailyCostTracker,
    get_adapter,
    _adapter_instances,
)
from backend.models import LLMCost


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
        return {"labels": labels, "usage": {"prompt_tokens": tokens, "completion_tokens": 0}}


@pytest.fixture
def engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr("backend.llm_adapter.get_session", get_session_override)
    return engine


def test_retries(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 10}}, fail_times=1)
    out = adapter.classify(["a"], job_id=1)
    assert out[0]["label"] == "x"
    assert adapter.calls == 2


def test_records_cost(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 10}})
    adapter.classify(["a"], job_id=1)
    with Session(engine) as session:
        entry = session.exec(select(LLMCost)).one()
        assert entry.job_id == 1
        assert entry.tokens_in == 10
        assert entry.tokens_out == 0
        assert entry.estimated_cost_gbp == pytest.approx(
            10 / 1000 * adapter.price_per_1k_tokens_gbp
        )


def test_cost_limit(engine, monkeypatch):
    tracker = DailyCostTracker(limit=0.0001)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 1000}})
    with pytest.raises(RuntimeError):
        adapter.classify(["a"], job_id=1)
    with Session(engine) as session:
        assert session.exec(select(LLMCost)).first() is None


def test_batches_prompts_exceed_batch_size(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    responses = {
        p: {"label": p, "confidence": 1.0, "tokens": 1}
        for p in ["a", "b", "c", "d", "e"]
    }
    adapter = DummyAdapter(responses)
    prompts = list(responses.keys())
    adapter.classify(prompts, job_id=1)
    expected_calls = (len(prompts) + adapter.batch_size - 1) // adapter.batch_size
    assert adapter.calls == expected_calls


def test_job_cost_cap(engine, monkeypatch):
    tracker = DailyCostTracker(limit=100.0, job_limit=5.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)

    class CostlyAdapter(AbstractAdapter):
        price_per_1k_tokens_gbp = 1.0

        def _send(self, prompts):
            return {"labels": [("x", 1.0)] * len(prompts), "usage": {"prompt_tokens": 3000, "completion_tokens": 0}}

    adapter = CostlyAdapter("m")
    adapter.classify(["a"], job_id=1)
    with pytest.raises(RuntimeError):
        adapter.classify(["b"], job_id=1)


def test_logs_cost(engine, monkeypatch, caplog):
    tracker = DailyCostTracker(limit=100.0, job_limit=5.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 100}})
    with caplog.at_level("INFO"):
        adapter.classify(["a"], job_id=1)
    assert any("cost" in r.message for r in caplog.records)


def test_report_cost_recorded(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    with tracker.track(job_id=1, cost=0.2):
        pass
    with Session(engine) as session:
        entry = session.exec(select(LLMCost)).one()
        assert entry.job_id == 1
        assert entry.tokens_in == 0
        assert entry.tokens_out == 0
        assert entry.estimated_cost_gbp == pytest.approx(0.2)


def test_report_cost_limit(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0, job_limit=0.3)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    with tracker.track(job_id=1, cost=0.2):
        pass
    with pytest.raises(RuntimeError):
        with tracker.track(job_id=1, cost=0.2):
            pass
    with Session(engine) as session:
        entries = list(session.exec(select(LLMCost)))
        assert len(entries) == 1


def test_provider_selected_via_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    _adapter_instances.clear()
    adapter = get_adapter()
    assert isinstance(adapter, AnthropicAdapter)


def test_provider_selected_via_config(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    config = tmp_path / "cfg.json"
    config.write_text(json.dumps({"llm_provider": "azure"}))
    monkeypatch.setenv("LLM_CONFIG_FILE", str(config))
    _adapter_instances.clear()
    adapter = get_adapter()
    assert isinstance(adapter, AzureAdapter)
